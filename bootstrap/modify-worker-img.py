#!/usr/bin/env python3

import boto3
import yaml
import sys
import os
import time


print("START.")
print(time.ctime())

#defaults
input_file="jupyter.yaml"

#input_file
try:
    input_file=sys.argv[1]
except:
    print("define input file!")
    sys.exit(1)


#custom image
custom_image=None
try:
    custom_image=sys.argv[2]
except:
    pass
    
#aws region
try:
    aws_region=sys.argv[3]
except:
    print("define aws_region!")
    sys.exit(1)

#output_file
try:
    output_file=sys.argv[4]
except:
    print("define output file!")
    sys.exit(1)

node_capacity_min=3
try:
    node_capacity_min=sys.argv[5]
except:
    print("define node_capacity_min!")
    pass

#DASKExtraCondaPackages_NO_WHITESPACE
DASKExtraCondaPackages_NO_WHITESPACE=""
try:
    DASKExtraCondaPackages_NO_WHITESPACE=sys.argv[6].replace(","," ")
except:
    pass

#DASKExtraPipPackages_NO_WHITESPACE
DASKExtraPipPackages_NO_WHITESPACE=""
try:
    DASKExtraPipPackages_NO_WHITESPACE=sys.argv[7].replace(","," ")
except:
    pass


with open(input_file,"r") as f:
  yl=yaml.safe_load_all(f.read())

dask=list(yl)

if custom_image:
    print("Set image to: ", custom_image)
    dask[0]['spec']['template']['spec']['containers'][0]['image']=custom_image

print("Set POD volume mounts ...")
dask[0]['spec']['template']['spec']['containers'][0]['volumeMounts']=[{'mountPath': '/home/jovyan/work', 'name': 's3fsmount'}]

print("Set S3FS mounts ...")
dask[0]['spec']['template']['spec']['volumes']=[{'name': 's3fsmount', 'hostPath': {'path': '/mnt/s3fs'}}]

if DASKExtraCondaPackages_NO_WHITESPACE:
    print("Install extra Conda packages: ", DASKExtraCondaPackages_NO_WHITESPACE)
    if 'env' in dask[0]['spec']['template']['spec']['containers'][0]:
        dask[0]['spec']['template']['spec']['containers'][0]['env'].append({"name":"EXTRA_CONDA_PACKAGES", "value":DASKExtraCondaPackages_NO_WHITESPACE})
    else:
        dask[0]['spec']['template']['spec']['containers'][0]['env']=[{"name":"EXTRA_CONDA_PACKAGES", "value":DASKExtraCondaPackages_NO_WHITESPACE}]

if DASKExtraPipPackages_NO_WHITESPACE:
    print("Install extra Python PIP packages: ", DASKExtraPipPackages_NO_WHITESPACE)
    if 'env' in dask[0]['spec']['template']['spec']['containers'][0]:
        dask[0]['spec']['template']['spec']['containers'][0]['env'].append({"name":"EXTRA_PIP_PACKAGES", "value":DASKExtraPipPackages_NO_WHITESPACE})
    else:
        dask[0]['spec']['template']['spec']['containers'][0]['env']=[{"name":"EXTRA_PIP_PACKAGES", "value":DASKExtraPipPackages_NO_WHITESPACE}]

print("Set initial node capacity: ", node_capacity_min)
dask[0]['spec']['replicas']=int(node_capacity_min)

out=yaml.safe_dump_all(dask, default_flow_style=False)
print(out)
with open(output_file,"w") as f:
  f.write(out)

sys.exit(0)
