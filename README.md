This is a [Next.js](https://nextjs.org) project with a Python webhook handler for Benchling Canvas integrations.

## Project Structure

```
vercel-lambda/
├── app/                    # Next.js frontend application
├── api/                    # Python webhook handlers
│   ├── webhook.py         # Main webhook handler
│   ├── benchling_client.py # Benchling client initialization
│   ├── canvas_blocks.py   # UI block builders and constants
│   ├── canvas_updater.py  # Canvas update utilities
│   ├── requirements.txt   # Python dependencies
│   └── runtime.txt        # Python version specification
├── manifest.yaml           # Benchling app manifest
└── vercel.json            # Vercel deployment config
```

## Environment Variables

Before deploying, set up the following **required** environment variables in Vercel:

```bash
BENCHLING_URL=https://your-tenant.benchling.com
BENCHLING_CLIENT_ID=your_client_id_here
BENCHLING_CLIENT_SECRET=your_client_secret_here
```

**Note:** All three variables are required. The application will fail to start if any are missing.

### Setting Environment Variables in Vercel

1. Go to your project settings in Vercel
2. Navigate to "Environment Variables"
3. Add each variable for Production, Preview, and Development environments
4. Get credentials from your Benchling App Configuration page

## Getting Started

First, install dependencies:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Webhook Handler

The Python webhook handler (`api/webhook.py`) processes Benchling Canvas events:

### Supported Events

- **v2.canvas.created**: Initializes a new canvas with UI blocks
- **v2.canvas.userInteracted**: Handles button clicks and user interactions

### Webhook URL

After deployment, configure your Benchling app to send webhooks to:
```
https://your-app.vercel.app/api/webhook
```

### Handler Features

- Uses Benchling SDK with `CanvasBuilder`
- OAuth2 client credentials authentication
- Dynamic canvas updates with section UI blocks
- Button handlers: Add Item, Remove Item, Submit
- Error handling and logging

### Customization

The codebase is organized into reusable modules:

**`api/webhook.py`** - Main webhook handler
- Edit TODO sections in handler methods:
  - `handle_add_item()` - Add your item creation logic
  - `handle_remove_item()` - Add your item removal logic
  - `handle_submit()` - Add your submission/processing logic

**`api/benchling_client.py`** - Client initialization
- Manages OAuth2 authentication
- Reads credentials from environment variables

**`api/canvas_blocks.py`** - UI block builders
- `get_initial_canvas_blocks()` - Initial canvas layout
- `create_success_section()` - Success message blocks
- `create_error_section()` - Error message blocks
- Customize button IDs and labels here

**`api/canvas_updater.py`** - Canvas update utilities
- `update_canvas()` - Updates canvas with new blocks
- Uses CanvasBuilder pattern

## Deploy on Vercel

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Deploy:
   ```bash
   vercel --prod
   ```

3. Set environment variables in Vercel dashboard

4. Configure webhook URL in Benchling app settings

Check out [Vercel deployment documentation](https://vercel.com/docs) for more details.
