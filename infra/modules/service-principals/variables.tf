variable "name_prefix" {
  description = "Prefix for the display names, for example dataforge-dev."
  type        = string
}

variable "learner_count" {
  description = "Number of learner principals. Use one for each worker."
  type        = number
  default     = 1

  validation {
    condition     = var.learner_count >= 1 && var.learner_count <= 20
    error_message = "Use 1 to 20 learner principals."
  }
}
