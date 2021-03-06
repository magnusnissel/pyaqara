"""Aqara Client Test"""
# pylint: disable=protected-access
import json

from unittest.mock import MagicMock
from aqara.client import AqaraClient
from aqara.gateway import AqaraGateway
from aqara.const import (
    AQARA_EVENT_NEW_GATEWAY
)

# Send tests

def test_discover_gateways():
    """Test if the correct message is sent for discover_gateways."""
    mock_client = AqaraClient()
    mock_client.broadcast = MagicMock()

    mock_client.discover_gateways()

    cmd_whois = {"cmd": "whois"}
    mock_client.broadcast.assert_called_with(cmd_whois)

def test_discover_devices():
    """Test if the correct message is sent for discover_devices."""
    mock_client = AqaraClient()
    mock_client.unicast = MagicMock()
    gw_addr = "10.10.10.10"
    cmd_get_id_list = {"cmd": "get_id_list"}

    mock_client.discover_devices(gw_addr)

    mock_client.unicast.assert_called_with(gw_addr, cmd_get_id_list)

def test_read_device():
    """Test if the correct message is sent for read_device."""
    mock_client = AqaraClient()
    mock_client.unicast = MagicMock()
    gw_addr = "10.10.10.10"
    test_sid = "123456"

    mock_client.read_device(gw_addr, test_sid)

    expected_data = {"cmd": "read", "sid": test_sid}
    mock_client.unicast.assert_called_with(gw_addr, expected_data)

def test_handle_message_iam():
    """Test if a gateway is created and discover_devices is called with gateway IP
    after message "iam" is received"""

    src_addr = "10.10.10.10"
    msg_iam = {
        "cmd": "iam",
        "ip": src_addr,
        "sid": "123456"
    }

    mock_handler = MagicMock()
    client = AqaraClient()
    client.subscribe(mock_handler)

    client.handle_message(msg_iam, src_addr)

    assert len(client.gateways.keys()) == 1
    new_gateway = client.gateways["123456"]
    mock_handler.assert_called_once_with(
        sender=client,
        gateway=new_gateway,
        signal=AQARA_EVENT_NEW_GATEWAY
    )

def test_handle_message_device_list():
    """Test if client maps all sids to the gateway and call gateway.on_devices_discovered"""

    gw_addr = "10.10.10.10"
    gw_sid = "123456"
    msg_get_id_list_ack = {
        "cmd": "get_id_list_ack",
        "sid": gw_sid,
        "data": json.dumps(["1", "2", "3"])
    }

    mock_client = AqaraClient()
    mock_client.read_device = MagicMock()
    mock_gateway = AqaraGateway(mock_client, gw_sid, gw_addr, None)
    mock_client._gateways[gw_sid] = mock_gateway
    mock_gateway.on_devices_discovered = MagicMock()

    mock_client.handle_message(msg_get_id_list_ack, gw_addr)

    mock_gateway.on_devices_discovered.called_once_with(["1", "2", "3"])
    assert len(mock_client._device_to_gw.keys()) == 3

def test_handle_message_read_ack():
    """Test if client forward the read_ack to the correct gateway"""
    gw_addr = "10.10.10.10"
    gw_sid = "123456"
    device_sid = "abcdef"

    mock_client = AqaraClient()
    mock_gateway = AqaraGateway(mock_client, gw_sid, gw_addr, None)
    mock_gateway.on_read_ack = MagicMock()
    mock_client._gateways[gw_sid] = mock_gateway
    mock_client._device_to_gw[gw_sid] = mock_gateway
    mock_client._device_to_gw[device_sid] = mock_gateway
    msg_read_ack = {
        "cmd": "read_ack",
        "sid": device_sid,
        "model": "magnet",
        "data": json.dumps({"status": "open"})
    }

    mock_client.handle_message(msg_read_ack, gw_addr)

    mock_gateway.on_read_ack.assert_called_once_with("magnet", device_sid, {"status": "open"})

def test_handle_message_heartbeat():
    """Test if the gateway token is updated on a gateway heartbeat"""
    gw_addr = "10.10.10.10"
    gw_sid = "123456"
    mock_client = AqaraClient()
    mock_gateway = AqaraGateway(mock_client, gw_sid, gw_addr, None)
    mock_gateway.on_device_heartbeat = MagicMock()
    mock_client._gateways[gw_sid] = mock_gateway
    mock_client._device_to_gw[gw_sid] = mock_gateway
    msg_heartbeat = {
        "cmd": "heartbeat",
        "model": "gateway",
        "sid": gw_sid,
        "token": "ffffff",
        "data": json.dumps({"ip": gw_addr})
    }

    mock_client.handle_message(msg_heartbeat, gw_addr)

    mock_gateway.on_device_heartbeat.assert_called_once_with(
        "gateway", gw_sid, {"ip": gw_addr}, "ffffff"
    )
