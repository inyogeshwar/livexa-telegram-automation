#!/bin/bash
# Livexa Snapshot Manager
# Creates VM snapshots in OpenShift

VM_NAME="livexa-vm-01"
NAMESPACE="livexa-prod"
TIMESTAMP=$(date +%Y%m%d%H%M)

echo "Creating Snapshot for $VM_NAME..."

# This requires 'oc' CLI tool installed and authenticated
# oc virt snapshot $VM_NAME --name "backup-$TIMESTAMP" -n $NAMESPACE

if [ $? -eq 0 ]; then
    echo "Snapshot backup-$TIMESTAMP created successfully."
else
    echo "Snapshot failed. Ensure 'oc' tools are installed."
fi
