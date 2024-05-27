package trivy

ignore[reason] {
    finding := input[0].Results[_].Secrets[_]
    finding.Target == "/app/fetch_shopify_data.py"
    finding.Title == "Google (GCP) Service-account"
    reason := "Ignore specific GCP service-account secret in fetch_shopify_data.py"
}