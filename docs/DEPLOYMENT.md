# Deployment Guide for Google Cloud Run

## Prerequisites

1. Google Cloud Platform account with billing enabled
2. gcloud CLI installed and configured
3. Domain name (optional, for custom HTTPS)
4. Git repository with the project

## Step 1: GCP Project Setup

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"

gcloud projects create $PROJECT_ID --name="Microservices SRE"
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  compute.googleapis.com