'use client';

import { type ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  ChevronDown,
  Sparkles,
  Upload,
  Download,
  RefreshCw,
  Check,
} from 'lucide-react';

interface FormState {
  watchImage: File | null;
  brandingImage: File | null;
  dialImage: File | null;
  selectedStyle: string;
  modelProvider: string;
  outputCount: number;
  creativeDirection: string;
  advancedExpanded: boolean;
  brandMode: string;
  dialReferenceMode: string;
  productStrength: number;
  sceneCreativity: number;
  backgroundStyle: string;
  customBackground: string;
  cameraAngle: string;
  lightingStyle: string;
  supportingProps: string[];
  negativePrompt: string;
  aspectRatio: string;
  qualityMode: string;
  isGenerating: boolean;
  generatedCount: number;
}

interface GeneratedImage {
  variant: number;
  url: string;
  prompt?: string;
  provider?: string;
}


const ACTIVE_STYLE = {
  id: 'velvet-cloth-background',
  name: 'Velvet cloth background',
  description: 'Preserve the watch exactly; replace only the background with velvet cloth.',
};

const MODEL_OPTIONS = [
  {
    group: 'OpenAI',
    options: ['gpt-image-1', 'gpt-image-2', 'dall-e-2', 'dall-e-3'],
  },
  {
    group: 'Google',
    options: ['gemini-3.1-flash-image-preview', 'gemini-3-pro-image-preview', 'imagen-4.0-ultra-generate-001'],
  },
];

const DIAL_REFERENCE_MODE_OPTIONS = [
  {
    id: 'off',
    name: 'Off',
    description: 'No extra dial reference is used.',
  },
  {
    id: 'balanced',
    name: 'Balanced dial protection',
    description: 'Use the optional dial close-up to improve dial accuracy while keeping the full watch photo primary.',
  },
  {
    id: 'aggressive',
    name: 'Aggressive dial protection',
    description: 'Use the optional dial close-up very strongly for maximum dial text, minute-track, and hand-position fidelity.',
  },
];

// -----------------------------------------------------------------------------
// Old style presets are intentionally commented out, not deleted.
// Re-enable later if you want multiple style presets again.
//
// const STYLE_OPTIONS = [
//   { id: 'flat-lay', name: 'Luxury Flat Lay', description: 'Birds-eye view arrangement' },
//   { id: 'open-box', name: 'Open Box Product Shot', description: 'Unboxing presentation' },
//   { id: 'dark-studio', name: 'Dark Premium Studio', description: 'High-end dark background' },
//   { id: 'ecommerce', name: 'E-commerce Listing', description: 'Online marketplace style' },
//   { id: 'editorial', name: 'Editorial Campaign', description: 'Magazine-style layout' },
//   { id: 'macro-detail', name: 'Macro Detail Shot', description: 'Close-up craftsmanship details' },
// ];
// -----------------------------------------------------------------------------

function backendStyleReferenceCandidates(baseUrl: string, rawName: string) {
  const encodedName = encodeURIComponent(rawName);

  return [
    `${baseUrl}/style_references/${encodedName}.png`,
    `${baseUrl}/style-reference-images/${encodedName}.png`,
    `${baseUrl}/style-reference-images/velvet-cloth-background/${encodedName}.png`,
  ];
}

function ImageWithFallback({
  srcs,
  alt,
  className,
  fallback,
}: {
  srcs: string[];
  alt: string;
  className: string;
  fallback: ReactNode;
}) {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    setActiveIndex(0);
  }, [srcs.join('|')]);

  if (!srcs.length || activeIndex >= srcs.length) {
    return <>{fallback}</>;
  }

  return (
    <img
      src={srcs[activeIndex]}
      alt={alt}
      className={className}
      onError={() => setActiveIndex(prev => prev + 1)}
    />
  );
}

export default function AlienTimeStudio() {
  const [formState, setFormState] = useState<FormState>({
    watchImage: null,
    brandingImage: null,
    dialImage: null,
    selectedStyle: ACTIVE_STYLE.id,
    modelProvider: 'gpt-image-1',
    outputCount: 4,
    creativeDirection: '',
    advancedExpanded: false,
    brandMode: 'visual-reference',
    dialReferenceMode: 'off',
    productStrength: 100,
    sceneCreativity: 15,
    backgroundStyle: 'green-velvet',
    customBackground: '',
    cameraAngle: 'auto',
    lightingStyle: 'soft-studio',
    supportingProps: [],
    negativePrompt: '',
    aspectRatio: '1:1',
    qualityMode: 'ultra',
    isGenerating: false,
    generatedCount: 0,
  });

  const [generatedImages, setGeneratedImages] = useState<GeneratedImage[]>([]);
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const heroVariationImages = useMemo(
    () => ['cover 2', 'cover 3', 'cover 4', 'cover 5'].map(name =>
      backendStyleReferenceCandidates(apiBaseUrl, name)
    ),
    [apiBaseUrl]
  );

  const watchInputRef = useRef<HTMLInputElement>(null);
  const brandingInputRef = useRef<HTMLInputElement>(null);
  const dialInputRef = useRef<HTMLInputElement>(null);

  const getImagePreviewUrl = (file: File | null) => {
    return file ? URL.createObjectURL(file) : '';
  };

  const handleFileUpload = (file: File, type: 'watch' | 'branding' | 'dial') => {
    if (type === 'watch') {
      setFormState(prev => ({ ...prev, watchImage: file }));
    } else if (type === 'branding') {
      setFormState(prev => ({ ...prev, brandingImage: file }));
    } else {
      setFormState(prev => ({ ...prev, dialImage: file }));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent, type: 'watch' | 'branding' | 'dial') => {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0], type);
    }
  };

  const handleGenerate = async () => {
    console.log('[Frontend] Generate button clicked');

    if (!formState.watchImage) {
      console.warn('[Frontend] Missing required watch image', {
        hasWatchImage: Boolean(formState.watchImage),
        hasBrandingImage: Boolean(formState.brandingImage),
        hasDialImage: Boolean(formState.dialImage),
      });
      alert('Please upload the watch image');
      return;
    }

    if (formState.dialReferenceMode !== 'off' && !formState.dialImage) {
      alert('Please upload the dial close-up image or switch Dial Reference Mode to Off.');
      return;
    }

    const endpoint = `${apiBaseUrl}/generate`;

    const formData = new FormData();
    formData.append('watch_image', formState.watchImage);
    if (formState.brandingImage) {
      formData.append('branding_image', formState.brandingImage);
    }
    if (formState.dialImage) {
      formData.append('dial_image', formState.dialImage);
    }
    formData.append('selected_style', ACTIVE_STYLE.id);
    formData.append('model_provider', formState.modelProvider);
    formData.append('output_count', String(formState.outputCount));
    formData.append('creative_direction', formState.creativeDirection || '');
    formData.append('brand_mode', formState.brandMode);
    formData.append('dial_reference_mode', formState.dialReferenceMode);
    formData.append('product_strength', String(formState.productStrength));
    formData.append('scene_creativity', String(formState.sceneCreativity));
    formData.append('background_style', formState.backgroundStyle);
    formData.append('custom_background', formState.customBackground || '');
    formData.append('camera_angle', formState.cameraAngle);
    formData.append('lighting_style', formState.lightingStyle);
    formData.append('supporting_props', JSON.stringify([]));
    formData.append('negative_prompt', formState.negativePrompt || '');
    formData.append('aspect_ratio', formState.aspectRatio);
    formData.append('quality_mode', formState.qualityMode);

    console.log('[Frontend] Sending generation request', {
      endpoint,
      watchImage: formState.watchImage.name,
      brandingImage: formState.brandingImage?.name || null,
      dialImage: formState.dialImage?.name || null,
      outputCount: formState.outputCount,
      selectedStyle: ACTIVE_STYLE.id,
      modelProvider: formState.modelProvider,
      brandMode: formState.brandMode,
      dialReferenceMode: formState.dialReferenceMode,
      backgroundStyle: formState.backgroundStyle,
      cameraAngle: formState.cameraAngle,
      lightingStyle: formState.lightingStyle,
      aspectRatio: formState.aspectRatio,
      qualityMode: formState.qualityMode,
    });

    setFormState(prev => ({ ...prev, isGenerating: true, generatedCount: 0 }));
    setGeneratedImages([]);

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      console.log('[Frontend] Backend response status', response.status);
      const data = await response.json();
      console.log('[Frontend] Backend response body', data);

      if (!response.ok) {
        throw new Error(data?.detail || `Failed to generate images with ${formState.modelProvider}. It might be unavailable.`);
      }

      const images = Array.isArray(data.images) ? data.images : [];
      setGeneratedImages(images);
      setFormState(prev => ({
        ...prev,
        isGenerating: false,
        generatedCount: images.length,
      }));

      const generatedSection = document.getElementById('generated-variations');
      generatedSection?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      console.error('[Frontend] Generation failed', error);
      setFormState(prev => ({ ...prev, isGenerating: false, generatedCount: 0 }));
      alert(error instanceof Error ? `${error.message}\n\nIf the model failed to load, please try selecting a different model.` : 'Something went wrong while generating images. The model might be unavailable.');
    }
  };

  const useRecommendedPrompt = () => {
    setFormState(prev => ({
      ...prev,
      creativeDirection:
        'Replace only the background behind and around the uploaded watch with premium green velvet cloth. Preserve the watch itself exactly: same case shape, same bracelet, same dial color, same brand name text, same minute-track lines, same indices, same numbers, same hands, same date, and the exact same time shown on the watch. If a dial close-up is uploaded, use it aggressively to keep the dial ultra sharp, readable under zoom, and free from blurred, tilted, bent, or deformed text. Do not add a box, papers, cards, extra objects, hands, or another watch. Make the velvet realistic with soft folds, luxury fabric texture, natural shadows, and sharp commercial product photography quality.',
    }));
  };

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    element?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="relative min-h-screen bg-background">
      <nav className="sticky top-0 z-50 border-b border-border bg-white/70 backdrop-blur-md supports-[backdrop-filter]:bg-white/50">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-foreground">AlienTime Studio</span>
          </div>

          <div className="hidden items-center gap-8 md:flex">
            <button
              onClick={() => scrollToSection('how-it-works')}
              className="text-sm font-medium text-foreground/70 hover:text-foreground transition"
            >
              How it works
            </button>            <button
              onClick={() => scrollToSection('generate')}
              className="text-sm font-medium text-foreground/70 hover:text-foreground transition"
            >
              Generate
            </button>
          </div>

          <Button
            onClick={() => scrollToSection('generate')}
            className="bg-gradient-to-r from-primary to-secondary text-white hover:shadow-lg transition-shadow"
          >
            Start Generating
          </Button>
        </div>
      </nav>

      <main className="relative z-10">
        <section className="relative overflow-hidden px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-12 md:grid-cols-2 md:gap-8 items-center">
              <div className="space-y-6">
                <h1 className="text-4xl font-bold leading-tight text-foreground sm:text-5xl lg:text-6xl text-balance">
                  Create Watch Product Photos with AI
                </h1>
                <p className="text-lg text-foreground/70 text-balance">
                  Upload your full watch image, optionally upload a close-up dial photo for extra accuracy, choose the image model,
                  and generate premium velvet-cloth background variations while preserving the watch, dial, text, minute-track lines,
                  date, and time as accurately as possible.
                </p>
                <div className="flex gap-4 pt-4">
                  <Button
                    onClick={() => scrollToSection('generate')}
                    size="lg"
                    className="bg-gradient-to-r from-primary to-secondary text-white hover:shadow-lg transition-all"
                  >
                    Start Generating
                  </Button>
                  <Button
                    onClick={() => scrollToSection('how-it-works')}
                    variant="outline"
                    size="lg"
                    className="border-border hover:bg-muted"
                  >
                    How It Works
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {heroVariationImages.map((srcs, index) => (
                  <div
                    key={index}
                    className="aspect-square overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-primary/10 to-secondary/10"
                  >
                    <ImageWithFallback
                      srcs={srcs}
                      alt={`Velvet reference ${index + 1}`}
                      className="h-full w-full object-cover"
                      fallback={
                        <div className="flex h-full items-center justify-center p-4 text-center">
                          <div className="space-y-2">
                            <Sparkles className="h-8 w-8 text-primary/50 mx-auto" />
                            <p className="text-sm text-foreground/50">Velvet reference {index + 1}</p>
                          </div>
                        </div>
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="generate" className="relative px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl">
            <div className="mb-8 text-center">
              <h2 className="text-3xl font-bold text-foreground sm:text-4xl">Generate Velvet Product Shoot</h2>
            </div>

            <Card className="border-border shadow-lg p-8 space-y-8">
              <div className="grid grid-cols-1 items-stretch gap-8 md:grid-cols-3">
                <div className="flex h-full flex-col space-y-4">
                  <div className="min-h-[84px]">
                    <label className="text-sm font-semibold text-foreground">Upload Watch/Product Image</label>
                    <p className="text-sm text-foreground/60">
                      Upload the main watch photo. The backend prompt is designed to preserve the watch itself and change only the background.
                    </p>
                  </div>
                  <div
                    onDragOver={handleDragOver}
                    onDrop={e => handleDrop(e, 'watch')}
                    onClick={() => watchInputRef.current?.click()}
                    className="flex min-h-[210px] flex-1 items-center justify-center rounded-2xl border-2 border-dashed border-primary/30 bg-primary/5 p-6 text-center cursor-pointer hover:border-primary/50 hover:bg-primary/10 transition"
                  >
                    <input
                      ref={watchInputRef}
                      type="file"
                      accept=".png,.jpg,.jpeg,.webp"
                      onChange={e => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'watch')}
                      className="hidden"
                    />
                    {formState.watchImage ? (
                      <div className="space-y-3">
                        <div className="flex justify-center">
                          <div className="relative h-40 w-full max-w-xs overflow-hidden rounded-xl border border-primary/20 bg-white">
                            <img
                              src={getImagePreviewUrl(formState.watchImage)}
                              alt="Uploaded watch preview"
                              className="h-full w-full object-contain"
                            />
                          </div>
                        </div>
                        <p className="truncate text-sm font-medium text-foreground">{formState.watchImage.name}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={e => {
                            e.stopPropagation();
                            setFormState(prev => ({ ...prev, watchImage: null }));
                          }}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="h-8 w-8 text-primary/50 mx-auto" />
                        <p className="text-sm font-medium text-foreground">Drag and drop or click to upload</p>
                        <p className="text-xs text-foreground/50">PNG, JPG, JPEG, WEBP</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex h-full flex-col space-y-4">
                  <div className="min-h-[84px]">
                    <label className="text-sm font-semibold text-foreground">Upload Cloth / Branding Image <span className="text-xs font-normal text-foreground/50">(Optional)</span></label>
                    <p className="text-sm text-foreground/60">
                      Optional. Upload a cloth or branding reference if you want the background styling or branding to follow a reference image.
                    </p>
                  </div>
                  <div
                    onDragOver={handleDragOver}
                    onDrop={e => handleDrop(e, 'branding')}
                    onClick={() => brandingInputRef.current?.click()}
                    className="flex min-h-[210px] flex-1 items-center justify-center rounded-2xl border-2 border-dashed border-secondary/30 bg-secondary/5 p-6 text-center cursor-pointer hover:border-secondary/50 hover:bg-secondary/10 transition"
                  >
                    <input
                      ref={brandingInputRef}
                      type="file"
                      accept=".png,.jpg,.jpeg,.webp"
                      onChange={e => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'branding')}
                      className="hidden"
                    />
                    {formState.brandingImage ? (
                      <div className="space-y-3">
                        <div className="flex justify-center">
                          <div className="relative h-40 w-full max-w-xs overflow-hidden rounded-xl border border-secondary/20 bg-white">
                            <img
                              src={getImagePreviewUrl(formState.brandingImage)}
                              alt="Uploaded branding preview"
                              className="h-full w-full object-contain"
                            />
                          </div>
                        </div>
                        <p className="truncate text-sm font-medium text-foreground">{formState.brandingImage.name}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={e => {
                            e.stopPropagation();
                            setFormState(prev => ({ ...prev, brandingImage: null }));
                          }}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="h-8 w-8 text-secondary/50 mx-auto" />
                        <p className="text-sm font-medium text-foreground">Drag and drop or click to upload</p>
                        <p className="text-xs text-foreground/50">PNG, JPG, JPEG, WEBP • Optional</p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex h-full flex-col space-y-4">
                  <div className="min-h-[84px]">
                    <label className="text-sm font-semibold text-foreground">Upload Dial Close-up <span className="text-xs font-normal text-foreground/50">(Optional)</span></label>
                    <p className="text-sm text-foreground/60">
                      Optional but recommended for maximum dial accuracy. Upload a close-up of the dial to help preserve the brand name, minute-track lines, inner text, indices, and exact hand positions.
                    </p>
                  </div>
                  <div
                    onDragOver={handleDragOver}
                    onDrop={e => handleDrop(e, 'dial')}
                    onClick={() => dialInputRef.current?.click()}
                    className="flex min-h-[210px] flex-1 items-center justify-center rounded-2xl border-2 border-dashed border-emerald-400/40 bg-emerald-50 p-6 text-center cursor-pointer hover:border-emerald-500/60 hover:bg-emerald-100/70 transition"
                  >
                    <input
                      ref={dialInputRef}
                      type="file"
                      accept=".png,.jpg,.jpeg,.webp"
                      onChange={e => e.target.files?.[0] && handleFileUpload(e.target.files[0], 'dial')}
                      className="hidden"
                    />
                    {formState.dialImage ? (
                      <div className="space-y-3">
                        <div className="flex justify-center">
                          <div className="relative h-40 w-full max-w-xs overflow-hidden rounded-xl border border-emerald-400/30 bg-white">
                            <img
                              src={getImagePreviewUrl(formState.dialImage)}
                              alt="Uploaded dial preview"
                              className="h-full w-full object-contain"
                            />
                          </div>
                        </div>
                        <p className="truncate text-sm font-medium text-foreground">{formState.dialImage.name}</p>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={e => {
                            e.stopPropagation();
                            setFormState(prev => ({ ...prev, dialImage: null, dialReferenceMode: 'off' }));
                          }}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="h-8 w-8 text-emerald-500/70 mx-auto" />
                        <p className="text-sm font-medium text-foreground">Drag and drop or click to upload</p>
                        <p className="text-xs text-foreground/50">PNG, JPG, JPEG, WEBP • Optional</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1">
                  <label className="text-sm font-semibold text-foreground">Active Style</label>
                  <p className="text-sm text-foreground/60">
                    The old multi-style presets are disabled for now. The active style is a single generic velvet-cloth background pipeline.
                  </p>
                </div>
                <div className="rounded-xl border-2 border-primary bg-primary/5 p-4">
                  <p className="text-sm font-semibold text-foreground">{ACTIVE_STYLE.name}</p>
                  <p className="mt-1 text-sm text-foreground/60">{ACTIVE_STYLE.description}</p>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <label className="text-sm font-semibold text-foreground">Models</label>
                  <select
                    value={formState.modelProvider}
                    onChange={e => setFormState(prev => ({ ...prev, modelProvider: e.target.value }))}
                    className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                  >
                    {MODEL_OPTIONS.map(group => (
                      <optgroup key={group.group} label={group.group}>
                        {group.options.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                <div className="space-y-4">
                  <label className="text-sm font-semibold text-foreground">Dial Reference Mode</label>
                  <select
                    value={formState.dialReferenceMode}
                    onChange={e => setFormState(prev => ({ ...prev, dialReferenceMode: e.target.value }))}
                    className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                  >
                    {DIAL_REFERENCE_MODE_OPTIONS.map(option => (
                      <option key={option.id} value={option.id}>{option.name}</option>
                    ))}
                  </select>
                  <p className="text-xs text-foreground/60">
                    {DIAL_REFERENCE_MODE_OPTIONS.find(option => option.id === formState.dialReferenceMode)?.description}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <label className="text-sm font-semibold text-foreground">Output Count</label>
                <select
                  value={formState.outputCount}
                  onChange={e => setFormState(prev => ({ ...prev, outputCount: parseInt(e.target.value) }))}
                  className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                >
                  <option value={1}>1</option>
                  <option value={2}>2</option>
                  <option value={4}>4</option>
                </select>
              </div>

              <div className="space-y-4">
                <label className="text-sm font-semibold text-foreground">Creative Direction</label>
                <textarea
                  value={formState.creativeDirection}
                  onChange={e => setFormState(prev => ({ ...prev, creativeDirection: e.target.value }))}
                  placeholder="Example: Replace only the background with deep green velvet cloth and preserve the exact dial, minute track, brand name, date, and hand positions."
                  rows={4}
                  className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground placeholder:text-foreground/40 hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition resize-none"
                />
                <Button
                  onClick={useRecommendedPrompt}
                  variant="outline"
                  size="sm"
                  className="border-border hover:bg-primary/10 hover:text-primary hover:border-primary"
                >
                  Use Recommended Prompt
                </Button>
                <p className="text-xs text-foreground/50">
                  If a dial close-up image is uploaded and Dial Reference Mode is not Off, the backend will aggressively emphasize dial fidelity in the prompt.
                </p>
              </div>

              <div className="space-y-4 border-t border-border pt-8">
                <button
                  onClick={() => setFormState(prev => ({ ...prev, advancedExpanded: !prev.advancedExpanded }))}
                  className="flex items-center gap-2 font-semibold text-foreground hover:text-primary transition"
                >
                  Advanced Options
                  <ChevronDown
                    className={`h-5 w-5 transition-transform ${formState.advancedExpanded ? 'rotate-180' : ''}`}
                  />
                </button>

                {formState.advancedExpanded && (
                  <div className="space-y-6 pt-4 border-t border-border">
                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Cloth / Branding Integration Mode</label>
                      <select
                        value={formState.brandMode}
                        onChange={e => setFormState(prev => ({ ...prev, brandMode: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                      >
                        <option value="visual-reference">Use uploaded cloth/branding as visual reference</option>
                        <option value="visible">Place branding clearly on cloth if possible</option>
                        <option value="subtle">Subtle branding only</option>
                        <option value="none">No branding</option>
                      </select>
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">
                        Product Preservation Strength: {formState.productStrength}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={formState.productStrength}
                        onChange={e => setFormState(prev => ({ ...prev, productStrength: parseInt(e.target.value) }))}
                        className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                      <p className="text-xs text-foreground/60">Keep this high for maximum watch preservation.</p>
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Scene Creativity: {formState.sceneCreativity}%</label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={formState.sceneCreativity}
                        onChange={e => setFormState(prev => ({ ...prev, sceneCreativity: parseInt(e.target.value) }))}
                        className="w-full h-2 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                      <p className="text-xs text-foreground/60">Keep this low if you want very strict preservation.</p>
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Background Style</label>
                      <select
                        value={formState.backgroundStyle}
                        onChange={e => setFormState(prev => ({ ...prev, backgroundStyle: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                      >
                        <option value="green-velvet">Green velvet</option>
                        <option value="black-velvet">Black velvet</option>
                        <option value="blue-velvet">Blue velvet</option>
                        <option value="burgundy-velvet">Burgundy velvet</option>
                        <option value="custom">Custom</option>
                      </select>
                      {formState.backgroundStyle === 'custom' && (
                        <Input
                          placeholder="Describe custom velvet background"
                          value={formState.customBackground}
                          onChange={e => setFormState(prev => ({ ...prev, customBackground: e.target.value }))}
                          className="mt-2 border-border"
                        />
                      )}
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Camera Angle</label>
                      <select
                        value={formState.cameraAngle}
                        onChange={e => setFormState(prev => ({ ...prev, cameraAngle: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                      >
                        <option value="auto">Auto (preserve original)</option>
                        <option value="top-down">Top-down</option>
                        <option value="45-degree">45-degree</option>
                        <option value="front-facing">Front-facing</option>
                        <option value="macro">Macro</option>
                      </select>
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Lighting Style</label>
                      <select
                        value={formState.lightingStyle}
                        onChange={e => setFormState(prev => ({ ...prev, lightingStyle: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                      >
                        <option value="soft-studio">Soft studio lighting</option>
                        <option value="cinematic">Cinematic</option>
                        <option value="bright">Bright commercial</option>
                        <option value="warm">Warm luxury lighting</option>
                        <option value="auto">Auto</option>
                      </select>
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Negative Prompt</label>
                      <textarea
                        value={formState.negativePrompt}
                        onChange={e => setFormState(prev => ({ ...prev, negativePrompt: e.target.value }))}
                        placeholder="Things to avoid: blurred dial, tilted brand text, deformed minute track, changed hands, changed time, unreadable text, distorted watch geometry…"
                        rows={3}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground placeholder:text-foreground/40 hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition resize-none"
                      />
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Aspect Ratio</label>
                      <select
                        value={formState.aspectRatio}
                        onChange={e => setFormState(prev => ({ ...prev, aspectRatio: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                      >
                        <option value="1:1">1:1 Square</option>
                        <option value="4:5">4:5 Instagram Portrait</option>
                        <option value="16:9">16:9 Landscape</option>
                        <option value="3:2">3:2 Product Photo</option>
                      </select>
                    </div>

                    <div className="space-y-3">
                      <label className="text-sm font-semibold text-foreground">Quality Mode</label>
                      <select
                        value={formState.qualityMode}
                        onChange={e => setFormState(prev => ({ ...prev, qualityMode: e.target.value }))}
                        className="w-full rounded-lg border border-border bg-white px-4 py-2 text-sm text-foreground hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition"
                      >
                        <option value="standard">Standard</option>
                        <option value="high">High</option>
                        <option value="ultra">Ultra</option>
                      </select>
                      <p className="text-xs text-foreground/50">
                        Ultra mode is recommended for the sharpest dial detail and highest text fidelity.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-border">
                <Button
                  onClick={handleGenerate}
                  disabled={formState.isGenerating}
                  size="lg"
                  className="w-full cursor-pointer bg-gradient-to-r from-primary to-secondary text-white hover:shadow-lg transition-all disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {formState.isGenerating ? (
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Generating velvet watch photos…
                    </div>
                  ) : (
                    `Generate ${formState.outputCount} Product Photo${formState.outputCount !== 1 ? 's' : ''}`
                  )}
                </Button>
              </div>
            </Card>
          </div>
        </section>

        <section id="generated-variations" className="relative px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <h2 className="mb-8 text-3xl font-bold text-foreground sm:text-4xl">Generated Variations</h2>

            {generatedImages.length === 0 ? (
              <Card className="border-border p-12 text-center">
                <Sparkles className="h-12 w-12 text-primary/30 mx-auto mb-4" />
                <p className="text-lg text-foreground/60">Your generated product photos will appear here.</p>
              </Card>
            ) : (
              <div className={`grid gap-6 ${generatedImages.length === 1 ? 'grid-cols-1' : generatedImages.length === 2 ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'}`}>
                {generatedImages.map(image => (
                  <Card key={image.variant} className="border-border overflow-hidden hover:shadow-lg transition">
                    <div className="aspect-square bg-gradient-to-br from-primary/10 to-secondary/10 overflow-hidden">
                      <img
                        src={image.url}
                        alt={`Variation ${image.variant}`}
                        className="h-full w-full object-cover"
                      />
                    </div>
                    <div className="p-4 space-y-3">
                      <div className="inline-block rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                        Variation {image.variant}
                      </div>
                      <div className="text-xs text-foreground/50">{image.provider || formState.modelProvider}</div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1 cursor-pointer border-border hover:bg-primary/10 hover:text-primary hover:border-primary"
                          onClick={() => window.open(image.url, '_blank')}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1 cursor-pointer border-border hover:bg-primary/10 hover:text-primary hover:border-primary"
                          onClick={handleGenerate}
                        >
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Regenerate
                        </Button>
                      </div>
                      <Button variant="ghost" size="sm" className="w-full cursor-pointer text-primary hover:bg-primary/10">
                        Use This
                      </Button>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        </section>

        <section id="how-it-works" className="relative px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-6xl">
            <h2 className="mb-8 text-3xl font-bold text-foreground sm:text-4xl text-center">How It Works</h2>

            <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
              {[
                { icon: Upload, title: 'Upload Watch Image', desc: 'Upload your full watch photo' },
                { icon: Upload, title: 'Optional Cloth Reference', desc: 'Upload cloth / branding image if needed' },
                { icon: Upload, title: 'Optional Dial Close-up', desc: 'Use a close-up dial image for higher dial fidelity' },
                { icon: Check, title: 'Generate Photos', desc: 'Create premium velvet background variations' },
              ].map((step, i) => {
                const Icon = step.icon;
                return (
                  <Card key={i} className="border-border text-center p-8 hover:shadow-lg transition">
                    <div className="flex justify-center mb-4">
                      <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                        <Icon className="h-8 w-8 text-white" />
                      </div>
                    </div>
                    <h3 className="font-semibold text-foreground mb-2">{step.title}</h3>
                    <p className="text-sm text-foreground/60">{step.desc}</p>
                  </Card>
                );
              })}
            </div>
          </div>
        </section>

        <footer className="border-t border-border bg-white/50 backdrop-blur-sm px-4 py-12 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <div className="mb-8 text-center">
              <p className="text-sm text-foreground/70 font-medium">AlienTime Studio — AI Product Photography Generator</p>
            </div>
            <div className="flex justify-center gap-6">
              <a href="#" className="text-sm text-foreground/60 hover:text-foreground transition">
                Privacy
              </a>
              <a href="#" className="text-sm text-foreground/60 hover:text-foreground transition">
                Terms
              </a>
              <a href="#" className="text-sm text-foreground/60 hover:text-foreground transition">
                Contact
              </a>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
