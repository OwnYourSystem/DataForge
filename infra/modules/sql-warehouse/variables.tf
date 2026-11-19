variable "name" {
  description = "Name of the SQL warehouse."
  type        = string
}

variable "principals" {
  description = "Application ids of the service principals that can use the warehouse."
  type        = list(string)
}

variable "cluster_size" {
  description = "Warehouse size. The smallest size is sufficient for lesson data."
  type        = string
  default     = "2X-Small"
}

variable "max_num_clusters" {
  description = "Upper limit of clusters. This is also a cost limit."
  type        = number
  default     = 1
}

variable "auto_stop_mins" {
  description = "Minutes without a query before the warehouse stops."
  type        = number
  default     = 5
}
