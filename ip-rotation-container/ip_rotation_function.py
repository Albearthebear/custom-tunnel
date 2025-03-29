#!/usr/bin/env python3
"""
Google Cloud Function for Custom Tunnel IP Rotation

This script rotates the IP address of a GCP VM running a custom tunnel service.
It's designed to be triggered manually.

Rotation process:
1. Reserve a new static IP address in the project
2. Assign the new IP to the VM
3. Release old IP immediately if specified

Prerequisites:
- Service account with appropriate permissions
- VM instance running the tunnel
- Compute Engine API enabled
"""

import time
import logging
import os
from datetime import datetime
from googleapiclient import discovery
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ip-rotation")

# Configuration (can be overridden by environment variables)
PROJECT_ID = os.environ.get("PROJECT_ID", "custom-tunnel-project")
REGION = os.environ.get("REGION", "europe-west4")
ZONE = os.environ.get("ZONE", "europe-west4-a")
INSTANCE_NAME = os.environ.get("INSTANCE_NAME", "custom-tunnel-server")

def reserve_static_ip(compute, project_id, region, name):
    """Reserve a new static IP address in the project"""
    logger.info(f"Reserving new static IP: {name}")
    
    address_body = {
        "name": name,
        "addressType": "EXTERNAL",
        "description": f"Tunnel IP created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    
    operation = compute.addresses().insert(
        project=project_id, 
        region=region, 
        body=address_body
    ).execute()
    
    # Wait for operation to complete
    while True:
        result = compute.regionOperations().get(
            project=project_id,
            region=region,
            operation=operation['name']
        ).execute()
        
        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            break
        
        time.sleep(1)
    
    # Get the reserved IP address
    address = compute.addresses().get(
        project=project_id,
        region=region,
        address=name
    ).execute()
    
    logger.info(f"Reserved IP: {address['address']}")
    return address['address']

def get_current_ip_name(compute, project_id, zone, instance_name):
    """Get the name of the currently assigned static IP"""
    logger.info(f"Getting current IP information for {instance_name}")
    
    instance = compute.instances().get(
        project=project_id,
        zone=zone,
        instance=instance_name
    ).execute()
    
    access_configs = instance['networkInterfaces'][0]['accessConfigs']
    if not access_configs:
        logger.warning("No access configs found on the instance")
        return None
    
    # Try to find the name of the address from the addresses list
    current_nat_ip = access_configs[0].get('natIP')
    if not current_nat_ip:
        logger.warning("No external IP currently assigned")
        return None
    
    # List all addresses to find the one matching our current IP
    addresses = compute.addresses().list(
        project=project_id,
        region=REGION
    ).execute().get('items', [])
    
    for address in addresses:
        if address.get('address') == current_nat_ip:
            logger.info(f"Current IP name: {address['name']}")
            return address['name']
    
    logger.warning(f"Could not find static IP name for {current_nat_ip}")
    return None
    
def assign_ip_to_vm(compute, project_id, zone, instance_name, ip_address):
    """Assign a static IP address to a VM instance"""
    logger.info(f"Assigning IP {ip_address} to {instance_name}")
    
    # First, get the current instance info
    instance = compute.instances().get(
        project=project_id,
        zone=zone,
        instance=instance_name
    ).execute()
    
    # Delete the current access config
    if instance['networkInterfaces'][0].get('accessConfigs'):
        compute.instances().deleteAccessConfig(
            project=project_id,
            zone=zone,
            instance=instance_name,
            accessConfig='External NAT',
            networkInterface='nic0'
        ).execute()
    
    # Add the new access config with our reserved IP
    access_config_body = {
        "name": "External NAT",
        "natIP": ip_address,
        "type": "ONE_TO_ONE_NAT"
    }
    
    operation = compute.instances().addAccessConfig(
        project=project_id,
        zone=zone,
        instance=instance_name,
        networkInterface='nic0',
        body=access_config_body
    ).execute()
    
    # Wait for operation to complete
    while True:
        result = compute.zoneOperations().get(
            project=project_id,
            zone=zone,
            operation=operation['name']
        ).execute()
        
        if result['status'] == 'DONE':
            if 'error' in result:
                raise Exception(result['error'])
            break
        
        time.sleep(1)
    
    logger.info(f"Successfully assigned IP {ip_address} to {instance_name}")

def release_ip(compute, project_id, region, ip_name):
    """Release a static IP address"""
    logger.info(f"Releasing IP: {ip_name}")
    
    try:
        operation = compute.addresses().delete(
            project=project_id,
            region=region,
            address=ip_name
        ).execute()
        
        # Wait for operation to complete
        while True:
            result = compute.regionOperations().get(
                project=project_id,
                region=region,
                operation=operation['name']
            ).execute()
            
            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                break
            
            time.sleep(1)
        
        logger.info(f"Successfully released IP {ip_name}")
        return True
    except HttpError as e:
        logger.error(f"Error releasing IP {ip_name}: {e}")
        return False

def rotate_ip(request):
    """Main function to handle IP rotation requests"""
    request_json = request.get_json(silent=True)
    
    # Check if this is a release request
    if request_json and request_json.get('action') == 'release':
        project_id = request_json.get('project_id', PROJECT_ID)
        region = request_json.get('region', REGION)
        ip_name = request_json.get('ip_name')
        
        if not ip_name:
            return "No IP name provided for release", 400
            
        compute = discovery.build('compute', 'v1')
        result = release_ip(compute, project_id, region, ip_name)
        return f"IP release {'successful' if result else 'failed'}"
    
    # Regular rotation request
    logger.info("Starting IP rotation process")
    
    # Initialize Google API client
    compute = discovery.build('compute', 'v1')
    
    # Get current IP name
    current_ip_name = get_current_ip_name(compute, PROJECT_ID, ZONE, INSTANCE_NAME)
    
    # Reserve new IP
    new_ip_name = f"tunnel-ip-{int(time.time())}"
    new_ip = reserve_static_ip(compute, PROJECT_ID, REGION, new_ip_name)
    
    # Assign new IP to VM
    assign_ip_to_vm(compute, PROJECT_ID, ZONE, INSTANCE_NAME, new_ip)
    
    # Release old IP if requested and if it exists
    release_old_ip = request_json and request_json.get('release_old_ip', False)
    if release_old_ip and current_ip_name:
        logger.info("Release of old IP requested")
        release_ip(compute, PROJECT_ID, REGION, current_ip_name)
    elif current_ip_name:
        logger.info(f"Old IP {current_ip_name} not released - manual release required")
    
    return f"IP rotation complete. New IP: {new_ip}"

# For local testing
if __name__ == "__main__":
    class FakeRequest:
        def get_json(self, silent=False):
            return None
    
    result = rotate_ip(FakeRequest())
    print(result) 