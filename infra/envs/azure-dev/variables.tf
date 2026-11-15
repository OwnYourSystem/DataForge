variable "subscription_id" {
  description = "Azure subscription for this environment. Use a personal subscription."
  type        = string
}

variable "environment" {
  description = "Short name of the environment. It is part of resource names."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z0-9]{2,8}$", var.environment))
    error_message = "Use 2 to 8 lowercase letters or digits."
  }
}

variable "location" {
  description = "Azure region. It must support serverless SQL warehouses."
  type        = string
  default     = "northeurope"
}

variable "catalog_name" {
  description = "Name of the lab catalog."
  type        = string
  default     = "dataforge_lab"
}

variable "learner_count" {
  description = "Number of learner principals. Use one for each worker."
  type        = number
  default     = 1
}

variable "warehouse_auto_stop_mins" {
  description = "Minutes without a query before the SQL warehouse stops."
  type        = number
  default     = 5
}
