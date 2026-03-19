import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.LIA_BACKEND_URL || "http://localhost:8000"

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/${id}`
    
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Error fetching pipeline template:", error)
    return NextResponse.json(
      { error: "Failed to fetch pipeline template" },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/${id}`
    
    const response = await fetch(url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify(body),
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Error updating pipeline template:", error)
    return NextResponse.json(
      { error: "Failed to update pipeline template" },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const url = `${BACKEND_URL}/api/v1/company/pipeline-templates/${id}`
    
    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    })
    
    const data = await response.json()
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error("Error deleting pipeline template:", error)
    return NextResponse.json(
      { error: "Failed to delete pipeline template" },
      { status: 500 }
    )
  }
}
