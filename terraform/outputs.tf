output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.app_eip.public_ip
}

output "instance_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = aws_instance.app_server.public_dns
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "Subnet ID"
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.app_sg.id
}

output "application_url" {
  description = "Application URL"
  value       = "http://${aws_eip.app_eip.public_ip}"
}

output "grafana_url" {
  description = "Grafana Dashboard URL"
  value       = "http://${aws_eip.app_eip.public_ip}:3000"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_eip.app_eip.public_ip}:9090"
}