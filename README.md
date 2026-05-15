# WristShot AI - For AlienTime Studio ⌚🤖

Elevate your e-commerce storefront with our cutting-edge AI image generator. Powered by OpenAI's advanced `gpt-image-1` API, this tool allows you to instantly create stunning, photorealistic product photography from simple text prompts and reference images. Bypass expensive photoshoots and generate studio-quality visuals in seconds.

## 🚀 Features

*   **High-Fidelity AI Rendering:** Utilizes OpenAI's `gpt-image-1` model tailored for precise macro and lifestyle watch photography.
*   **Multiple Scene Variants:** Generate Flat Lays, Open Box shots, Dark Studio setups, and clean E-commerce listings.
*   **Branding Integration:** Seamlessly maps custom branding (like branded cloths or cards) into the scene while maintaining the hero product's exact identity.
*   **Modern Frontend:** Built with Next.js 16, React 19, Tailwind CSS 4, and shadcn/ui for a sleek, responsive user experience.
*   **Robust Backend:** FastAPI Python server handling prompt generation, image processing, and API communication.

## 🛠️ Tech Stack

**Frontend:**
*   Next.js (App Router)
*   React 19
*   Tailwind CSS 4
*   Radix UI & shadcn/ui components
*   `pnpm` for package management

**Backend:**
*   Python
*   FastAPI & Uvicorn
*   OpenAI API

## ⚙️ Getting Started

### Prerequisites
*   Node.js (v18+)
*   Python 3.9+
*   `pnpm` package manager
*   An active OpenAI API Key

### 1. Clone the Repository
```bash
git clone https://github.com/talha-sattar/WristShot-AI-Watch-Image-Generator.git
cd WristShot-AI-Watch-Image-Generator
```

### 2. Backend Setup
Navigate to the backend directory (if separated) or root, and set up your Python environment:

```bash
cd backend
# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the backend directory with your OpenAI credentials:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_IMAGE_MODEL=gpt-image-1
```

Start the FastAPI server:
```bash
python -m uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

Get: https://pnpm.io/installation
Open a new terminal window, navigate to the root directory, and install the frontend dependencies:

```bash
pnpm install
```

Create a `.env.local` file in the root directory to link the frontend to your local API:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Start the Next.js development server:
```bash
pnpm dev
```

The application will now be running at `http://localhost:3000`.


```
