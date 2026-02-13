import { NextRequest, NextResponse } from 'next/server';

const DEFAULT_CONVERTER_BASE = 'https://latexonline.cc';

export async function GET() {
  return NextResponse.json({ ok: true, converter: process.env.LATEX_PDF_API_URL || DEFAULT_CONVERTER_BASE });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const latex = typeof body?.latex === 'string' ? body.latex : '';

    if (!latex.trim()) {
      return NextResponse.json({ error: 'latex is required' }, { status: 400 });
    }

    const base = process.env.LATEX_PDF_API_URL || DEFAULT_CONVERTER_BASE;
    const endpoint = `${base.replace(/\/+$/, '')}/compile?text=${encodeURIComponent(latex)}`;

    const response = await fetch(endpoint, {
      method: 'GET',
      cache: 'no-store',
    });

    const contentType = response.headers.get('content-type') || '';
    const bytes = await response.arrayBuffer();

    if (!response.ok || !contentType.includes('application/pdf')) {
      const errorText = new TextDecoder().decode(bytes).slice(0, 1000);
      return NextResponse.json(
        {
          error: 'LaTeX to PDF conversion failed',
          detail: errorText || `HTTP ${response.status}`,
        },
        { status: 502 }
      );
    }

    return new NextResponse(bytes, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="resume.pdf"',
      },
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unexpected error' },
      { status: 500 }
    );
  }
}
