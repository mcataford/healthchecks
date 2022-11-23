locals {
  service_name = "lambda-boilerplate"
}

locals {
  service_longname = "${var.env_name}_${local.service_name}"
}

locals {
  common_tags = {
    stack_name       = local.service_longname
    environment_name = var.env_name
    commit_sha       = var.commit_sha
  }
}
