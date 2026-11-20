export interface Endpoint {
  displayName: string;
  // Model sering endpoint name.
  endpointName: string;
}

export const ENDPOINTS: Endpoint[] = [
  {
    displayName: "Llama 4 Maverick",
    endpointName: "databricks-llama-4-maverick",
  },
  {
    displayName: "Llama 3.3 70B",
    endpointName: "databricks-meta-llama-3-3-70b-instruct",
  },
];
