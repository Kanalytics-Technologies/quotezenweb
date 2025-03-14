resource "aws_vpc" "main_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "main-vpc"
  }
}

variable "vpc_id" {
  default = aws_vpc.main_vpc.id
}

resource "aws_instance" "flask_ec2_quotezen" {
  ami                         = var.ami
  instance_type               = var.instance_type
  key_name                    = var.ssh_key_pair_name
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.flask_profile.name
  vpc_security_group_ids      = [aws_security_group.flask_sg.id]

  # Usa user_data en lugar de remote-exec para evitar reprovisionar
  user_data = <<-EOF
    #!/bin/bash
    export DEBIAN_FRONTEND=noninteractive

    # Actualizar paquetes
    sudo apt-get update -y && sudo apt-get upgrade -y

    # Instalar dependencias necesarias
    sudo apt-get install -y python3 python3-pip python3-venv git nginx unzip

    # Crear usuario para correr Flask
    sudo useradd -m -s /bin/bash flask_user || true
    sudo usermod -aG sudo flask_user

    # Clonar repo si no existe
    if [ ! -d "/home/flask_user/flask_app" ]; then
      sudo -u flask_user git clone ${var.github_repo} /home/flask_user/flask_app
    fi

    cd /home/flask_user/flask_app

    # Crear entorno virtual si no existe
    sudo -u flask_user python3 -m venv venv

    # Instalar dependencias
    sudo -u flask_user /home/flask_user/flask_app/venv/bin/pip install --upgrade pip
    sudo -u flask_user /home/flask_user/flask_app/venv/bin/pip install -r requirements.txt

    # Configurar Gunicorn
    sudo bash -c 'cat > /etc/systemd/system/flask_app.service <<EOF
    [Unit]
    Description=Gunicorn instance to serve Flask application
    After=network.target

    [Service]
    User=flask_user
    Group=flask_user
    WorkingDirectory=/home/flask_user/flask_app
    Environment="PATH=/home/flask_user/flask_app/venv/bin"
    ExecStart=/home/flask_user/flask_app/venv/bin/gunicorn -w 3 -b 0.0.0.0:8000 app:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    EOF'

    # Iniciar servicio Flask
    sudo systemctl daemon-reload
    sudo systemctl enable flask_app
    sudo systemctl restart flask_app

    # Configurar Nginx como proxy reverso
    sudo bash -c 'cat > /etc/nginx/sites-available/flask_app <<EOF
    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
    EOF'

    # Activar configuración y reiniciar Nginx
    sudo ln -s /etc/nginx/sites-available/flask_app /etc/nginx/sites-enabled/
    sudo systemctl restart nginx

    echo "🚀 Flask + Gunicorn + Nginx deployed!"
  EOF

  tags = {
    Name = "flask-ec2-quotezen"
  }
}

# **🔹 IAM Role para evitar credenciales en la instancia**
resource "aws_iam_role" "flask_role" {
  name = "flask_ec2_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_instance_profile" "flask_profile" {
  name = "flask_instance_profile"
  role = aws_iam_role.flask_role.name
}

# 🔹 **Security Group para Flask**
resource "aws_security_group" "flask_sg" {
  name        = "flask_sg"
  description = "Security group for Flask on EC2"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_ip] # ✅ Solo acceso SSH desde IP autorizada
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # ✅ Acceso HTTP para Nginx
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}