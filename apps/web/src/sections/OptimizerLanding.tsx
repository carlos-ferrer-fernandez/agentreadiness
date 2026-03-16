import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FileText, 
  Zap, 
  CheckCircle2, 
  ArrowRight,
  Download,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Loader2,
  Settings,
  Package
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'
import apiClient from '@/lib/api'
import { useUIStore } from '@/store'

const pricingTiers = [
  {
    name: 'Starter',
    price: 49,
    pages: 'Up to 25 pages',
    features: [
      'AI-optimized content',
      'Code examples added',
      'Structure improvements',
      'ZIP file delivery',
      'Implementation guide',
    ],
  },
  {
    name: 'Standard',
    price: 99,
    pages: 'Up to 50 pages',
    popular: true,
    features: [
      'Everything in Starter',
      'API reference tables',
      'Troubleshooting sections',
      'SEO optimization',
      'Priority support',
    ],
  },
  {
    name: 'Enterprise',
    price: 199,
    pages: 'Up to 100 pages',
    features: [
      'Everything in Standard',
      'Custom tone & style',
      'Multi-language support',
      '1-on-1 consultation',
      '30-day support',
    ],
  },
]

const optimizationStages = [
  { name: 'Crawling your docs', icon: FileText },
  { name: 'Analyzing structure', icon: Settings },
  { name: 'Generating improvements', icon: Zap },
  { name: 'Creating your package', icon: Package },
]

export function OptimizerLanding() {
  const { addNotification } = useUIStore()
  
  // Form state
  const [url, setUrl] = useState('')
  const [email, setEmail] = useState('')
  const [targetAudience, setTargetAudience] = useState('mixed')
  const [tone, setTone] = useState('friendly')
  const [priorities] = useState<string[]>(['code_examples'])
  
  // Pricing state
  const [estimatedPrice, setEstimatedPrice] = useState<number | null>(null)
  const [isEstimating, setIsEstimating] = useState(false)
  
  // Optimization state
  const [isOptimizing, setIsOptimizing] = useState(false)
  const [optimizationStage, setOptimizationStage] = useState(0)
  const [jobId, setJobId] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState(false)
  
  // FAQ state
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null)

  const handleGetEstimate = async () => {
    if (!url) return
    
    setIsEstimating(true)
    
    try {
      const response = await apiClient.post('/api/optimizer/pricing', { url })
      setEstimatedPrice(response.data.price_eur)
    } catch (error) {
      addNotification({ type: 'error', message: 'Failed to get estimate' })
    } finally {
      setIsEstimating(false)
    }
  }

  const handleStartOptimization = async () => {
    if (!url || !email) return
    
    setIsOptimizing(true)
    
    try {
      const response = await apiClient.post('/api/optimizer/start', {
        url,
        email,
        target_audience: targetAudience,
        tone,
        priorities,
      })
      
      setJobId(response.data.job_id)
      
      // Simulate progress (in production, poll the API)
      for (let i = 0; i < optimizationStages.length; i++) {
        setOptimizationStage(i)
        await new Promise(resolve => setTimeout(resolve, 2000))
      }
      
      setIsComplete(true)
      addNotification({ type: 'success', message: 'Optimization complete!' })
      
    } catch (error) {
      addNotification({ type: 'error', message: 'Failed to start optimization' })
      setIsOptimizing(false)
    }
  }

  const handleDownload = () => {
    if (jobId) {
      window.open(`/api/optimizer/download/${jobId}`, '_blank')
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                AI-Powered Documentation Optimization
              </span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6"
            >
              Get documentation that{' '}
              <span className="bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                AI agents love
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-muted-foreground mb-8"
            >
              We rewrite your documentation for AI agent consumption. 
              You get optimized markdown files, ready to deploy.
              <strong> Starting at €49.</strong>
            </motion.p>
          </div>
        </div>
      </section>

      {/* Main Form Section */}
      <section className="py-12 bg-muted/30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <Card className="overflow-hidden">
            <CardContent className="p-8">
              {!isOptimizing && !isComplete && (
                <div className="space-y-8">
                  {/* URL Input */}
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Your Documentation URL</label>
                    <div className="flex gap-3">
                      <Input
                        placeholder="https://docs.yourcompany.com"
                        value={url}
                        onChange={(e) => {
                          setUrl(e.target.value)
                          setEstimatedPrice(null)
                        }}
                        className="flex-1"
                      />
                      <Button 
                        onClick={handleGetEstimate}
                        disabled={!url || isEstimating}
                        variant="outline"
                      >
                        {isEstimating ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          'Get Estimate'
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Pricing Estimate */}
                  <AnimatePresence>
                    {estimatedPrice && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="bg-primary/5 rounded-lg p-6"
                      >
                        <div className="flex items-center justify-between mb-4">
                          <div>
                            <p className="text-sm text-muted-foreground">Estimated Price</p>
                            <p className="text-3xl font-bold">€{estimatedPrice}</p>
                          </div>
                          <Badge variant="secondary">One-time payment</Badge>
                        </div>
                        
                        {/* Customization Options */}
                        <div className="grid md:grid-cols-2 gap-4 mt-6">
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Target Audience</label>
                            <Select value={targetAudience} onValueChange={setTargetAudience}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="beginners">Beginners</SelectItem>
                                <SelectItem value="intermediate">Intermediate</SelectItem>
                                <SelectItem value="experts">Experts</SelectItem>
                                <SelectItem value="mixed">Mixed</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          
                          <div className="space-y-2">
                            <label className="text-sm font-medium">Tone</label>
                            <Select value={tone} onValueChange={setTone}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="formal">Formal</SelectItem>
                                <SelectItem value="casual">Casual</SelectItem>
                                <SelectItem value="technical">Technical</SelectItem>
                                <SelectItem value="friendly">Friendly</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>

                        {/* Email */}
                        <div className="space-y-2 mt-4">
                          <label className="text-sm font-medium">Email (for delivery)</label>
                          <Input
                            type="email"
                            placeholder="you@company.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                          />
                        </div>

                        {/* Start Button */}
                        <Button 
                          className="w-full mt-6" 
                          size="lg"
                          onClick={handleStartOptimization}
                          disabled={!email}
                        >
                          Start Optimization
                          <ArrowRight className="ml-2 w-4 h-4" />
                        </Button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Optimization Progress */}
              {isOptimizing && !isComplete && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h3 className="text-xl font-semibold mb-2">Optimizing Your Documentation</h3>
                    <p className="text-muted-foreground">This usually takes 2-5 minutes</p>
                  </div>
                  
                  <div className="space-y-4">
                    {optimizationStages.map((stage, index) => {
                      const StageIcon = stage.icon
                      const isActive = index === optimizationStage
                      const isComplete = index < optimizationStage
                      
                      return (
                        <div 
                          key={stage.name}
                          className={cn(
                            "flex items-center gap-3 p-3 rounded-lg transition-all",
                            isActive ? "bg-primary/10" : isComplete ? "bg-green-50" : "bg-muted"
                          )}
                        >
                          <div className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center",
                            isComplete ? "bg-green-500" : isActive ? "bg-primary" : "bg-muted-foreground/20"
                          )}>
                            {isComplete ? (
                              <CheckCircle2 className="w-4 h-4 text-white" />
                            ) : (
                              <StageIcon className={cn(
                                "w-4 h-4",
                                isActive ? "text-white" : "text-muted-foreground"
                              )} />
                            )}
                          </div>
                          <span className={cn(
                            "flex-1",
                            isActive && "font-medium"
                          )}>
                            {stage.name}
                          </span>
                          {isActive && (
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          )}
                        </div>
                      )
                    })}
                  </div>
                  
                  <Progress value={((optimizationStage + 1) / optimizationStages.length) * 100} />
                </div>
              )}

              {/* Complete */}
              {isComplete && (
                <div className="text-center space-y-6">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-8 h-8 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold mb-2">Your Documentation is Ready!</h3>
                    <p className="text-muted-foreground">
                      We've optimized your documentation and packaged it for you.
                    </p>
                  </div>
                  <Button size="lg" onClick={handleDownload}>
                    <Download className="mr-2 w-4 h-4" />
                    Download ZIP File
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    A copy has also been sent to {email}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-muted-foreground">
              Pay once, get optimized documentation. No subscriptions, no hidden fees.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingTiers.map((tier, index) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "bg-card rounded-xl border p-6 flex flex-col",
                  tier.popular && "border-primary ring-1 ring-primary shadow-lg scale-105"
                )}
              >
                {tier.popular && (
                  <Badge className="w-fit mb-4">Most Popular</Badge>
                )}
                <h3 className="text-lg font-semibold">{tier.name}</h3>
                <div className="mt-2 flex items-baseline">
                  <span className="text-3xl font-bold">€{tier.price}</span>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{tier.pages}</p>
                <ul className="mt-6 space-y-3 flex-1">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2 text-sm">
                      <CheckCircle2 className="w-5 h-5 text-primary flex-shrink-0" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button 
                  variant={tier.popular ? 'default' : 'outline'} 
                  className="w-full mt-6"
                  onClick={() => {
                    document.getElementById('optimizer-form')?.scrollIntoView({ behavior: 'smooth' })
                  }}
                >
                  Get Started
                </Button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground">
              Get AI-optimized documentation in 3 simple steps.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Submit Your Docs',
                description: 'Enter your documentation URL and preferences. We\'ll analyze the size and give you a price.',
              },
              {
                step: '2',
                title: 'AI Optimization',
                description: 'Our AI crawls, analyzes, and rewrites your documentation for maximum AI agent compatibility.',
              },
              {
                step: '3',
                title: 'Download & Deploy',
                description: 'Get optimized markdown files in a ZIP. Upload to your hosting platform and go live.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center"
              >
                <div className="w-12 h-12 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                <p className="text-muted-foreground">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {[
              {
                q: 'What do I get?',
                a: 'You get a ZIP file containing optimized markdown files, ready to deploy. Each file includes improved content, added code examples, better structure, and cross-links.',
              },
              {
                q: 'How long does it take?',
                a: 'Most optimizations complete in 2-5 minutes. Larger documentation sites may take up to 15 minutes.',
              },
              {
                q: 'What formats do you support?',
                a: 'We output standard Markdown files that work with any documentation platform: GitHub Pages, Netlify, Vercel, ReadMe, Docusaurus, etc.',
              },
              {
                q: 'Can I customize the output?',
                a: 'Yes! You can specify your target audience, tone of voice, and which sections to prioritize.',
              },
              {
                q: 'What if I\'m not satisfied?',
                a: 'We offer a 7-day money-back guarantee. If you\'re not happy with the results, contact us for a full refund.',
              },
            ].map((faq, index) => (
              <div key={index} className="border rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                  className="w-full flex items-center justify-between p-4 hover:bg-muted/50 transition-colors"
                >
                  <span className="font-medium text-left">{faq.q}</span>
                  {expandedFaq === index ? (
                    <ChevronUp className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  )}
                </button>
                <AnimatePresence>
                  {expandedFaq === index && (
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: 'auto' }}
                      exit={{ height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="p-4 pt-0 text-muted-foreground">
                        {faq.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-lg font-bold">AgentReadiness</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 AgentReadiness. All rights reserved.
            </p>
            <div className="flex gap-6">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Privacy
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Terms
              </a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground">
                Contact
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
