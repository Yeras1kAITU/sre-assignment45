terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "compute.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "servicenetworking.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

resource "google_compute_network" "main" {
  name                    = "microservices-vpc"
  auto_create_subnetworks = false
  routing_mode           = "REGIONAL"
}

resource "google_compute_subnetwork" "main" {
  name          = "microservices-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.main.id
  private_ip_google_access = true
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

resource "google_sql_database_instance" "postgres" {
  name             = "postgres-db"
  database_version = "POSTGRES_15"
  region           = var.region
  deletion_protection = false

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.main.id

      authorized_networks {
        name  = "cloud-run"
        value = "0.0.0.0/0"
      }
    }

    disk_size       = 20
    disk_type       = "PD_SSD"
    disk_autoresize = true
  }
}

resource "google_sql_database" "database" {
  name     = "microservices"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "admin" {
  name     = "admin"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

resource "google_redis_instance" "redis" {
  name           = "redis-memorystore"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
  authorized_network = google_compute_network.main.id
  connect_mode    = "DIRECT_PEERING"

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }
}

resource "google_compute_router" "router" {
  name    = "microservices-router"
  region  = var.region
  network = google_compute_network.main.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "microservices-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = "microservices-repo"
  format        = "DOCKER"

  depends_on = [google_project_service.services]
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "microservices-sa"
  display_name = "Microservices Service Account"
}

resource "google_project_iam_member" "cloud_run_sa_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/redis.viewer",
    "roles/run.invoker",
    "roles/artifactregistry.reader"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

output "project_id" {
  value = var.project_id
}

output "region" {
  value = var.region
}

output "database_connection_name" {
  value = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  value = google_redis_instance.redis.host
}