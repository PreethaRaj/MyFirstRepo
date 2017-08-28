/************************************************************************************************
 * This is my testcode to send data via serial port.
 * The code also receives the 'SENT' data, if pins 2 & 3 are connected with a jumper
 * Please choose the correct COM port, by verifying the device manager for assigned ports
 * Kindly choose the Desired Baud Rate and press "Connect", before sending the data.
 * ***********************************************************************************************/

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.IO.Ports;
using System.Threading;
using System.Windows.Threading;

namespace RS232
{
   
    public partial class MainWindow : Window
    {
        #region variables       
        FlowDocument mcFlowDoc = new FlowDocument();
        Paragraph para = new Paragraph();        
        SerialPort serial = new SerialPort();
        string recieved_data;
        #endregion

        public MainWindow()
        {
            InitializeComponent();
            InitializeComponent();           
            Connect_btn.Content = "Connect";
        }

        private void Connect_Comms(object sender, RoutedEventArgs e)
        {
            if (Connect_btn.Content == "Connect")
            {
                serial.PortName = Comm_Port_Names.Text;
                serial.BaudRate = Convert.ToInt32(Baud_Rates.Text);
                serial.Handshake = System.IO.Ports.Handshake.None;
                serial.Parity = Parity.None;
                serial.DataBits = 8;
                serial.StopBits = StopBits.One;
                serial.ReadTimeout = 200;
                serial.WriteTimeout = 50;
                serial.Open();

                Connect_btn.Content = "Disconnect";
                serial.DataReceived += new System.IO.Ports.SerialDataReceivedEventHandler(Recieve);

            }
            else
            {
                try 
                {
                    serial.Close();
                    Connect_btn.Content = "Connect";
                }
                catch
                {
                    int i = 0;
                }
            }
        }

        #region Recieving

        private delegate void UpdateUiTextDelegate(string text);
        private void Recieve(object sender, System.IO.Ports.SerialDataReceivedEventArgs e)
        {
            recieved_data = serial.ReadExisting(); 
            Dispatcher.Invoke(DispatcherPriority.Send, new UpdateUiTextDelegate(WriteData), recieved_data);
        }
        private void WriteData(string text)
        {
            para.Inlines.Add(text);
            mcFlowDoc.Blocks.Add(para);
            Commdata.Document = mcFlowDoc;
        }

        #endregion


        #region Sending        
        
        private void Send_Data(object sender, RoutedEventArgs e)
        {
            SerialCmdSend(SerialData.Text);
            SerialData.Text = "";
        }
        public void SerialCmdSend(string data)
        {
            if (serial.IsOpen)
            //serial.Open();
            //if (true)
            {
                try
                {
                    byte[] hexstring = Encoding.ASCII.GetBytes(data);
                    foreach (byte hexval in hexstring)
                    {
                        byte[] _hexval = new byte[] { hexval }; // convert byte to byte[] to write
                        //serial.Open();
                        serial.Write(_hexval, 0, 1);
                        Thread.Sleep(1);
                    }
                }
                catch (Exception ex)
                {
                    para.Inlines.Add("Failed to SEND" + data + "\n" + ex + "\n");
                    mcFlowDoc.Blocks.Add(para);
                    Commdata.Document = mcFlowDoc;
                }
            }
            else
            {
                int j = 0;
            }
        }

        #endregion
    }
}
