using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using UnityEngine;
using UnityEngine.InputSystem;

public class VRControllerSender : MonoBehaviour
{
    [SerializeField] private string ipAddress = "127.0.0.1";
    [SerializeField] private int port = 5555;
    [SerializeField] private int  publishFrameRate= 100;
    private float lastUpdateTime = 0f;
    private float targetInterval = 0f;

    [SerializeField] private GameObject controller;
    [SerializeField] private InputActionProperty trackingButton;
    [SerializeField] private InputActionProperty gripperButton;
    private bool trackingButtonTriggered = false;
    private bool gripperButtonTriggered = false;

    private TcpListener server;
    private TcpClient client;
    private NetworkStream stream;

    private bool isAwaitingConnection = false; // Track if waiting for a connection

    void Start()
    {
        StartServer();
        targetInterval = 1f / publishFrameRate;
    }

    void StartServer()
    {
        try
        {
            IPAddress ip = IPAddress.Parse(ipAddress);
            server = new TcpListener(ip, port);
            server.Start();
            Debug.Log($"Server started at {ipAddress}:{port}");
            WaitForClientConnection();
        }
        catch (Exception e)
        {
            Debug.LogError($"Server failed to start: {e.Message}");
        }
    }

    void WaitForClientConnection()
    {
        if (isAwaitingConnection) return;
        
        Debug.Log("Waiting for connection...");
        isAwaitingConnection = true;

        server.BeginAcceptTcpClient(OnClientConnected, null);
    }

    private void OnClientConnected(IAsyncResult ar)
    {
        isAwaitingConnection = false; // Mark that we're no longer awaiting a connection

        try
        {
            client = server.EndAcceptTcpClient(ar);
            stream = client.GetStream();
            Debug.Log("Client connected!");
        }
        catch (ObjectDisposedException)
        {
            // Debug.LogWarning("Server has been stopped. Ignoring client connection.");
        }
        catch (Exception e)
        {
            Debug.LogError($"Error accepting client connection: {e.Message}");
            WaitForClientConnection(); // Retry waiting for a new client
        }
    }

    void OnEnable()
    {
        trackingButton.action.performed += ctx => trackingButtonTriggered = true;
        gripperButton.action.performed += ctx => gripperButtonTriggered = true;
    }

    void OnDisable()
    {
        trackingButton.action.performed -= ctx => trackingButtonTriggered = true;
        gripperButton.action.performed -= ctx => gripperButtonTriggered = true;

        stream?.Close();
        client?.Close();
        server?.Stop();
    }

    void Update()
    {
        if (client == null || !client.Connected)
        {
            if (client != null)
            {
                client.Close();
                stream = null;
            }
            WaitForClientConnection();
            return;
        }
        if (Time.time - lastUpdateTime < targetInterval)
            return;
        lastUpdateTime = Time.time;

        // Get controller position and rotation
        // Convert to regular coordinate from Unity coordinate
        Vector3 position = controller.transform.position;
        Quaternion rotation = controller.transform.rotation;
        position = new Vector3(position.z, -position.x, position.y);
        rotation = new Quaternion(rotation.z, -rotation.x, rotation.y, -rotation.w);

        // Get button states
        bool button1 = trackingButtonTriggered;
        bool button2 = gripperButtonTriggered;

        // Create data string: x, y, z, qx, qy, qz, qw, button1, button2
        string FormatFloat(float value) => value.ToString("F3");
        string data = $"{FormatFloat(position.x)},{FormatFloat(position.y)},{FormatFloat(position.z)},{FormatFloat(rotation.x)},{FormatFloat(rotation.y)},{FormatFloat(rotation.z)},{FormatFloat(rotation.w)},{(button1 ? 1 : 0)},{(button2 ? 1 : 0)}\n";

        try
        {
            // Send data to the Python server
            byte[] message = Encoding.UTF8.GetBytes(data);
            stream.Write(message, 0, message.Length);
        }
        catch (Exception e)
        {
            Debug.Log($"Error writing to stream. Connection may lose: {e.Message}");
            client?.Close();
            stream = null; // Reset stream to handle reconnection
            WaitForClientConnection();
        }

        // Reset button states
        trackingButtonTriggered = false;
        gripperButtonTriggered = false;
    }
}
