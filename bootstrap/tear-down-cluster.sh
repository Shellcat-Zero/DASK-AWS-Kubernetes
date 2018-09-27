#!/bin/bash

AWSRegion=${1}

echo "TEAR DOWN START."

export KOPS_STATE_STORE=`cat /opt/kops-state/KOPS_STATE_STORE`
export KOPS_CLUSTER_NAME=`cat /opt/kops-state/KOPS_CLUSTER_NAME`
export AWS_DEFAULT_REGION=${AWSRegion}

kops export kubecfg --name $KOPS_CLUSTER_NAME

ingress=""
#delete ingresses
for i in `kubectl get ingress -o yaml | grep "name:" | grep -v hostname | awk '{print $2}'`; 
do 
  echo "Delete ingress: $i..."; 
  kubectl delete ingress $i --force;
  ingress="YES"
  sleep 10
  
  for j in `aws elbv2 describe-target-groups --region ${AWSRegion} --output text | grep arn | grep TARGETGROUPS | awk '{print $10}'`; 
  do
    echo "Target group: $j ..."; 
    N=`aws elbv2 describe-tags --resource-arns $j --region ${AWSRegion} --output text | grep $i`; 
    if [[ -n "${N}" ]];
    then
      echo "DELETE TARGET GROUP: ${N} ...";
      aws elbv2 delete-target-group --target-group-arn $j --region ${AWSRegion}
    fi
  done
done

#wait for target group deletion, it is async wait to remove ALB target groups
if [[ "${ingress}" == "YES" ]];
then
  sleep 20
fi

#delete cluster
kops delete cluster --name $KOPS_CLUSTER_NAME --yes >> /tmp/init-kops.log 2>&1

#delete local r53 dns zone
if [[ -e "/opt/kops-state/KOPS_R53_PRIVATE_HOSTED_ZONE_ID" ]];
then
  R53ZID=`cat /opt/kops-state/KOPS_R53_PRIVATE_HOSTED_ZONE_ID`
  if [[ -n ${R53ZID} ]];
  then
    aws route53 delete-hosted-zone --id ${R53ZID} --region ${AWSRegion}
  else
    echo "Missing R53 Zone ID!"
  fi
fi

#delete kops state bucket
S3BUCKET=`cat /opt/kops-state/KOPS_STATE_STORE | cut -d '/' -f 3`
./purge-s3-versioned-bucket.py ${S3BUCKET} ${AWSRegion}

#delete log group
LOG2=`cat /opt/kops-state/KOPS_AWSLOGS`
if [[ -n ${LOG2} ]];
then
  aws logs delete-log-group --log-group-name ${LOG2} --region ${AWSRegion}
fi

echo "TEAR DOWN DONE. EXIT 0"
exit 0
