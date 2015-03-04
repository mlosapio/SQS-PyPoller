# SQS-PyPoller
a simple python script to fetch messages from AWS SQS into local files or syslog

### Instructions
1. Make sure boto is installed (http://stackoverflow.com/questions/2481287/how-do-i-install-boto)
2. Create IAM user for this script (or use AWS role if running on an AWS instance). See IAM policy below.
3. Configure the poller.conf file with your credentials and other relevant options
4. Run the script:
a single run:
python poller.py

forever run:
python poller.py forever


### The needed AWS IAM policy for this script is:
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MySQSPollerScript",
      "Effect": "Allow",
      "Action": [
        "sqs:DeleteMessage",
        "sqs:GetQueueUrl",
        "sqs:ReceiveMessage"
      ],
      "Resource": [
        "arn:aws:sqs:us-east-1:YOUR_AWS_ACCOUNT_NUM:YOUR_SQS_QUEUE_NAME"
      ]
    }
  ]
}
```