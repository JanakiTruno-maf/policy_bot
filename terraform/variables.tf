variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "maf-policy-bot"
}

variable "rag_corpus_resource" {
  description = "RAG Corpus resource path"
  type        = string
  default     = ""
}