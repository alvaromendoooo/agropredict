# environments/local/variables.tf

variable "aemet_api_key" {
  description = "API key de AEMET"
  type        = string
  sensitive   = true
  default     = "fake-aemet-key-local" # valor por defecto para LocalStack
}

variable "itacyl_api_key" {
  description = "API key de ITACyL"
  type        = string
  sensitive   = true
  default     = "fake-itacyl-key-local"
}

variable "env_vars" {
  type  = map(string)
  sensitive = true
}
