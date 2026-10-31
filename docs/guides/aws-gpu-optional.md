# Optional. AWS credits for GPU hosting

Owner. Swayam only. One account is enough, so Disha and Udit can skip this.

## Do we need it

No. The dev GPU comes from RunPod (`runpod-dev-gpu.md`). AWS only matters for hosting the public demo cheaply. A GPU left on for judging costs real money on RunPod (about $0.59 to $0.89 per hour on Secure Cloud). The same hours on a `g4dn.xlarge` come out of the AWS credits, about $0.53 to $0.75 per hour in the sources we found. Do this after the RunPod pod works. Stop if it eats more than 30 minutes.

## What blocks a GPU on a new account

1. The Free account plan only includes "select AWS services" and excludes anything that could drain credits. Third-party sources say EC2 is limited to small types. The documented fix is upgrading to the Paid plan. Credits stay and apply to your bill. ([AWS plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html))
2. The EC2 quota "Running On-Demand G and VT instances" starts at 0 for new accounts and is adjustable ([EC2 quotas](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html)). AWS publishes no approval time. Small increases are often approved automatically, larger ones go to Support ([Service Quotas](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html)).

Side effect worth knowing. Free plan accounts are not eligible for other promotional credits. The extra challenge credits you mentioned may need the Paid plan.

## Steps

1. Console, Billing and Cost Management, Credits. Write down the balance, the expiry date and the list of applicable services. If EC2 is excluded there, stop here.
2. Create a budget alert first. Billing, Budgets, create a cost budget of about $20 with an email alert at 80 percent. After the upgrade, anything beyond the credits is charged to your card.
3. Upgrade. Open <https://console.aws.amazon.com/billing/home#/freetier/upgrade>, review the features and choose Upgrade account. A payment method must be on file.
4. Pick one region and stay in it. `ap-south-1` (Mumbai) is closest to judges in India. Check in the EC2 console that `g4dn.xlarge` is offered there before you request quota.
5. Request quota. Open <https://console.aws.amazon.com/servicequotas/home>, AWS services, Amazon EC2, search for "Running On-Demand G and VT instances". Choose Request increase at account-level, enter 4 (one `g4dn.xlarge` has 4 vCPUs), choose Request. Ask for 4, not 32. Small numbers are likelier to be approved automatically.
6. Track it under Request history. If it still says Pending after an hour or two, or it gets denied, open the Support case that the console links and say it is for a university hackathon demo.
7. When quota arrives, launch. EC2, Launch instance, an Ubuntu Deep Learning AMI with the NVIDIA driver and PyTorch (search "Deep Learning" in Quick Start), instance `g4dn.xlarge`, 100 GB gp3 disk, your key pair, a security group that opens 22 to your IP and the app port to the world. Attach an Elastic IP so the URL survives a stop and start.
8. SSH in and run the same steps as the RunPod bootstrap (`infra/runpod/bootstrap.sh` works as a template).
9. Stop the instance whenever it is idle. A stopped instance still bills for disk and any idle Elastic IP.

## Cost check

At the quoted rates, $100 of credit is about 130 to 190 instance hours. A 72 hour demo is about 38 to 54 dollars of that. These rates are from search results, not from the AWS pricing page, so confirm the price in the console before you launch.

## If it fails

Do not spend more time. Fall back to the plan in `PLAN.md` (Modal, then a RunPod pod during judging windows).
