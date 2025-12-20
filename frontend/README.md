# Professional RAG System - Frontend

## Overview

Modern, responsive Next.js frontend for the Professional RAG System with:
- Real-time chat interface
- Confidence score visualization
- Source citations display
- Conversational context support
- Built with shadcn/ui components

## Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8000 (or configured port)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local`:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1
```

### 3. Run Development Server

```bash
npm run dev
```

Visit http://localhost:3000

## Building for Production

```bash
# Build
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main chat page
│   └── globals.css         # Global styles
├── components/
│   ├── ui/                 # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── progress.tsx
│   │   ├── scroll-area.tsx
│   │   └── alert.tsx
│   └── chat/               # Chat-specific components
│       ├── ChatInterface.tsx
│       ├── MessageList.tsx
│       ├── MessageItem.tsx
│       ├── MessageInput.tsx
│       ├── ConfidenceIndicator.tsx
│       └── SourceCitation.tsx
├── hooks/
│   └── useChat.ts          # Chat state management hook
├── lib/
│   ├── api.ts              # API client
│   ├── types.ts            # TypeScript types
│   └── utils.ts            # Utility functions
└── package.json
```

## Features

### Chat Interface
- Real-time message exchange
- Auto-scroll to latest messages
- Loading indicators
- Error handling

### Confidence Scoring
- Visual progress bar
- Color-coded levels (high/medium/low)
- Percentage display

### Source Citations
- Clickable source references
- Relevance scores
- Text snippets
- Document and page information

## Customization

### Theme
Edit `app/globals.css` to customize colors:
```css
:root {
  --primary: 221.2 83.2% 53.3%;
  --secondary: 210 40% 96.1%;
  /* ... */
}
```

### API Endpoint
Update `.env.local`:
```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api.com
```

## Dependencies

- **Next.js 14**: React framework
- **shadcn/ui**: UI component library
- **TailwindCSS**: Utility-first CSS
- **Lucide React**: Icon library
- **React Markdown**: Markdown rendering

## Development

### Adding New Components

```bash
# Using shadcn/ui CLI (if installed)
npx shadcn-ui@latest add [component-name]
```

### Type Safety

All components use TypeScript for type safety. Types are defined in `lib/types.ts`.

## Troubleshooting

### API Connection Issues
- Ensure backend is running on configured port
- Check CORS settings in backend
- Verify `.env.local` has correct API URL

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### Style Issues
```bash
# Rebuild Tailwind
npm run dev
```

## License

MIT License - See LICENSE file for details
