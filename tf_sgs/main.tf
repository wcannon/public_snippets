# sg daas_automation
# inbound 443 and 24020 from daas_instances
resource "aws_security_group" "dass_instances" {
  name        = "daas_instances"
  description = "Allow administration of workspace pools and appstream instances"
  vpc_id      = var.vpcid

  tags = {
    Name = "daas_instances"
  }
}

# sg daas_instances
# inbound 5986 from daas_automation
resource "aws_security_group" "dass_automation" {
  name        = "daas_automation"
  description = "Automation EC2 Instances e.g. Ansible & Chocolatey"
  vpc_id      = var.vpcid

  tags = {
    Name = "daas_automation"
  }
}

resource "aws_vpc_security_group_ingress_rule" "dass_automation_ingress_winrm" {
  security_group_id = aws_security_group.dass_instances.id

  referenced_security_group_id = aws_security_group.dass_automation.id
  from_port                    = 5986
  ip_protocol                  = "tcp"
  to_port                      = 5986
}

resource "aws_vpc_security_group_ingress_rule" "dass_instances_ingress_ansible" {
  security_group_id = aws_security_group.dass_automation.id

  referenced_security_group_id = aws_security_group.dass_instances.id
  from_port                    = 443
  ip_protocol                  = "tcp"
  to_port                      = 443
}

resource "aws_vpc_security_group_ingress_rule" "dass_instances_ingress_chocolatey" {
  security_group_id = aws_security_group.dass_automation.id

  referenced_security_group_id = aws_security_group.dass_instances.id
  from_port                    = 24020
  ip_protocol                  = "tcp"
  to_port                      = 24020
}