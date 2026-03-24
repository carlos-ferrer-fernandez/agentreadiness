import { useState } from 'react'
import { motion } from 'framer-motion'
import { Zap, Send, ArrowLeft, Mail, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useNavigate } from 'react-router-dom'

export function Support() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const mailtoSubject = encodeURIComponent(subject || 'Support request from groundocs.com')
    const mailtoBody = encodeURIComponent(
      `Name: ${name}\nEmail: ${email}\n\n${message}`
    )
    window.location.href = `mailto:carlos@groundocs.com?subject=${mailtoSubject}&body=${mailtoBody}`
    setSubmitted(true)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b bg-background/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-14 items-center">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 hover:opacity-80 transition-opacity"
            >
              <div className="w-7 h-7 bg-forest rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold tracking-tight">GrounDocs</span>
            </button>

            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to home
            </button>
          </div>
        </div>
      </nav>

      {/* Support Form */}
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <div className="w-12 h-12 bg-forest/10 rounded-xl flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="w-6 h-6 text-forest" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-3">
            Get in touch
          </h1>
          <p className="text-muted-foreground text-lg">
            Have a question, issue, or feedback? We'd love to hear from you.
          </p>
        </motion.div>

        {submitted ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-12"
          >
            <div className="w-16 h-16 bg-forest/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Mail className="w-8 h-8 text-forest" />
            </div>
            <h2 className="text-2xl font-bold mb-3">Opening your email client...</h2>
            <p className="text-muted-foreground mb-2">
              Your email app should open with the message pre-filled.
            </p>
            <p className="text-muted-foreground text-sm mb-8">
              If it didn't open, you can email us directly at{' '}
              <a href="mailto:carlos@groundocs.com" className="text-forest hover:underline font-medium">
                carlos@groundocs.com
              </a>
            </p>
            <Button
              variant="outline"
              onClick={() => { setSubmitted(false); setName(''); setEmail(''); setSubject(''); setMessage('') }}
            >
              Send another message
            </Button>
          </motion.div>
        ) : (
          <motion.form
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            onSubmit={handleSubmit}
            className="space-y-5"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium mb-1.5">
                  Name
                </label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="rounded-lg"
                />
              </div>
              <div>
                <label htmlFor="email" className="block text-sm font-medium mb-1.5">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="rounded-lg"
                />
              </div>
            </div>

            <div>
              <label htmlFor="subject" className="block text-sm font-medium mb-1.5">
                Subject
              </label>
              <Input
                id="subject"
                type="text"
                placeholder="What's this about?"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                required
                className="rounded-lg"
              />
            </div>

            <div>
              <label htmlFor="message" className="block text-sm font-medium mb-1.5">
                Message
              </label>
              <textarea
                id="message"
                placeholder="Tell us how we can help..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
                rows={6}
                className="flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
              />
            </div>

            <Button
              type="submit"
              size="lg"
              className="w-full rounded-xl bg-forest hover:bg-forest-hover text-white h-12"
              disabled={!name || !email || !message}
            >
              <Send className="w-4 h-4 mr-2" />
              Send message
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              Or email us directly at{' '}
              <a href="mailto:carlos@groundocs.com" className="text-forest hover:underline">
                carlos@groundocs.com
              </a>
            </p>
          </motion.form>
        )}
      </div>

      {/* Footer */}
      <footer className="border-t py-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-forest rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-semibold">GrounDocs</span>
            </div>
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} GrounDocs
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
