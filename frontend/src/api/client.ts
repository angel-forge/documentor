import type { ApiErrorResponse } from "./types"

export const BASE_URL = import.meta.env.VITE_API_URL ?? "/api"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

function extractMessage(data: ApiErrorResponse): string {
  if (typeof data.detail === "string") {
    return data.detail
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => e.msg).join("; ")
  }
  return "An unexpected error occurred"
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const data = (await response.json()) as ApiErrorResponse
      message = extractMessage(data)
    } catch {
      // keep default message
    }
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)
  return handleResponse<T>(response)
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  return handleResponse<T>(response)
}

export async function apiPostForm<T>(
  path: string,
  formData: FormData,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: formData,
  })
  return handleResponse<T>(response)
}
