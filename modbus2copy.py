import configparser
import logging
import time
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Defaults

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read config file
def read_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    
    # Read values from config file
    modbus_config = {
        'source_host': config['modbus']['source_host'],
        'source_port': int(config['modbus']['source_port']),
        'destination_host': config['modbus']['destination_host'],
        'destination_port': int(config['modbus']['destination_port']),
        'register_type': config['modbus']['register_type'],
        'source_unit': int(config['modbus']['source_unit']),
        'source_address': int(config['modbus']['source_address']),
        'destination_unit': int(config['modbus']['destination_unit']),
        'destination_address': int(config['modbus']['destination_address']),
        'interval': int(config['modbus']['interval']),
    }
    
    return modbus_config

# Function to read registers from the source Modbus device
def read_registers(client, register_type, address, unit_id):
    if register_type == 'holding':
        result = client.read_holding_registers(address, 1, unit=unit_id)
    elif register_type == 'input':
        result = client.read_input_registers(address, 1, unit=unit_id)
    elif register_type == 'coil':
        result = client.read_coils(address, 1, unit=unit_id)
    else:
        logging.error(f"Unknown register type: {register_type}")
        return None
    
    if not result.isError():
        logging.info(f"Read value from {register_type} register at address {address}, unit {unit_id}: {result.registers[0]}")
        return result.registers[0]
    else:
        logging.error(f"Failed to read from {register_type} register at address {address}, unit {unit_id}")
        return None

# Function to write registers to the destination Modbus device
def write_registers(client, address, value, unit_id):
    result = client.write_register(address, value, unit=unit_id)
    if not result.isError():
        logging.info(f"Written value {value} to register at address {address}, unit {unit_id}")
    else:
        logging.error(f"Failed to write value {value} to register at address {address}, unit {unit_id}")

# Main logic
def main():
    config = read_config()

    while True:
        # Connect to the source host
        logging.info(f"Connecting to source host {config['source_host']}:{config['source_port']}")
        source_client = ModbusTcpClient(config['source_host'], port=config['source_port'])
        if not source_client.connect():
            logging.error(f"Failed to connect to source {config['source_host']}")
            time.sleep(config['interval'])
            continue
        
        # Read register value from the source
        value = read_registers(source_client, config['register_type'], config['source_address'], config['source_unit'])
        source_client.close()

        if value is None:
            time.sleep(config['interval'])
            continue
        
        # Connect to the destination host
        logging.info(f"Connecting to destination host {config['destination_host']}:{config['destination_port']}")
        destination_client = ModbusTcpClient(config['destination_host'], port=config['destination_port'])
        if not destination_client.connect():
            logging.error(f"Failed to connect to destination {config['destination_host']}")
            time.sleep(config['interval'])
            continue

        # Write register value to the destination
        write_registers(destination_client, config['destination_address'], value, config['destination_unit'])
        destination_client.close()

        # Wait until the interval condition is met (unixtime % interval == 0)
        logging.info(f"Waiting for the next interval: {config['interval']} seconds")
        time.sleep(1)
        while int(time.time()) % config['interval'] != 0:
            time.sleep(1)

if __name__ == "__main__":
    main()
