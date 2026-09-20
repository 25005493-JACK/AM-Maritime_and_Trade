import React, { useState } from 'react';
import { 
  X, 
  Minus, 
  Maximize2, 
  Paperclip, 
  Link2, 
  Smile, 
  Image, 
  Lock, 
  PenTool, 
  Trash2, 
  MoreVertical,
  ChevronDown,
  Sparkles
} from 'lucide-react';

export default function GmailComposeModal({
  isOpen,
  onClose,
  onSendEmail,
  initialTo = '',
  initialSubject = ''
}) {
  const [to, setTo] = useState(initialTo);
  const [subject, setSubject] = useState(initialSubject);
  const [body, setBody] = useState('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [attachments, setAttachments] = useState([]);

  if (!isOpen) return null;

  const handleSend = (e) => {
    e.preventDefault();
    if (onSendEmail) {
      onSendEmail({ to, subject, body, attachments });
    }
    // Reset form
    setTo('');
    setSubject('');
    setBody('');
    setAttachments([]);
    onClose();
  };

  const handleSimulateAttachment = () => {
    const sampleFiles = [
      'SI_Booking_5RUS-43614.pdf',
      'Bill_of_Lading_Draft_MONTER.docx',
      'Packing_List_Containers.xlsx'
    ];
    const randomFile = sampleFiles[Math.floor(Math.random() * sampleFiles.length)];
    if (!attachments.includes(randomFile)) {
      setAttachments([...attachments, randomFile]);
    }
  };

  return (
    <div className="fixed bottom-0 right-12 z-50 select-none animate-in slide-in-from-bottom-5 duration-200">
      <div 
        className={`w-[560px] rounded-t-xl shadow-2xl flex flex-col border transition-all duration-200 overflow-hidden ${
          isMinimized ? 'h-11' : 'h-[520px]'
        }`}
        style={{
          backgroundColor: 'var(--gmail-surface)',
          borderColor: 'var(--gmail-border)',
          color: 'var(--gmail-text)'
        }}
      >
        {/* Header Bar */}
        <div 
          className="h-10 px-4 border-b flex items-center justify-between cursor-pointer"
          style={{ 
            backgroundColor: 'var(--gmail-surface-variant)',
            borderColor: 'var(--gmail-border)' 
          }}
          onClick={() => setIsMinimized(!isMinimized)}
        >
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
            {subject || 'New Message'}
          </span>
          <div className="flex items-center space-x-1" onClick={(e) => e.stopPropagation()}>
            <button 
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 text-slate-600 dark:text-slate-400"
              title="Minimize"
            >
              <Minus className="w-3.5 h-3.5" />
            </button>
            <button 
              className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 text-slate-600 dark:text-slate-400"
              title="Full screen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
            <button 
              onClick={onClose}
              className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 text-slate-600 dark:text-slate-400"
              title="Save & close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Compose Form */}
        {!isMinimized && (
          <form onSubmit={handleSend} className="flex-1 flex flex-col justify-between overflow-hidden">
            <div className="flex-1 flex flex-col overflow-y-auto">
              
              {/* To field */}
              <div className="flex items-center px-4 py-2 border-b text-xs" style={{ borderColor: 'var(--gmail-border)' }}>
                <span className="text-slate-500 w-12 font-medium">To</span>
                <input
                  type="text"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  placeholder="Recipients (carrier, shipper, operations@port.com)..."
                  className="flex-1 bg-transparent text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none"
                  required
                />
                <div className="flex items-center space-x-2 text-slate-400 text-[11px]">
                  <span className="hover:underline cursor-pointer">Cc</span>
                  <span className="hover:underline cursor-pointer">Bcc</span>
                </div>
              </div>

              {/* Subject field */}
              <div className="flex items-center px-4 py-2 border-b text-xs" style={{ borderColor: 'var(--gmail-border)' }}>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Subject"
                  className="w-full bg-transparent text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none font-medium"
                  required
                />
              </div>

              {/* Attachments Chips */}
              {attachments.length > 0 && (
                <div className="flex flex-wrap gap-2 px-4 py-2 bg-slate-50 dark:bg-slate-900/50 border-b" style={{ borderColor: 'var(--gmail-border)' }}>
                  {attachments.map((file, idx) => (
                    <div key={idx} className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-950/60 border border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 text-xs">
                      <Paperclip className="w-3 h-3" />
                      <span className="truncate max-w-[200px]">{file}</span>
                      <button 
                        type="button" 
                        onClick={() => setAttachments(attachments.filter((_, i) => i !== idx))}
                        className="hover:text-red-500"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Message Body */}
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Write your email here, paste Shipping Instructions (SI) or request BL verification..."
                className="flex-1 p-4 bg-transparent text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none resize-none leading-relaxed"
              />
            </div>

            {/* Bottom Formatting & Action Bar */}
            <div className="px-4 py-3 border-t flex items-center justify-between" style={{ borderColor: 'var(--gmail-border)' }}>
              
              <div className="flex items-center space-x-2">
                {/* Send Button */}
                <div className="flex items-center rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-xs overflow-hidden transition">
                  <button
                    type="submit"
                    className="px-5 py-2 text-xs font-semibold tracking-wide cursor-pointer"
                  >
                    Send
                  </button>
                  <div className="h-5 w-px bg-blue-500" />
                  <button
                    type="button"
                    className="px-2 py-2 hover:bg-blue-800 cursor-pointer"
                    title="Schedule send"
                  >
                    <ChevronDown className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Formatting Tools */}
                <div className="flex items-center space-x-0.5 text-slate-500 dark:text-slate-400 pl-2">
                  <button type="button" className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Formatting options">
                    <span className="text-xs font-bold underline">A</span>
                  </button>
                  <button 
                    type="button" 
                    onClick={handleSimulateAttachment}
                    className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" 
                    title="Attach files (SI/BL)"
                  >
                    <Paperclip className="w-4 h-4" />
                  </button>
                  <button type="button" className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Insert link">
                    <Link2 className="w-4 h-4" />
                  </button>
                  <button type="button" className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Insert emoji">
                    <Smile className="w-4 h-4" />
                  </button>
                  <button type="button" className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Insert files using Drive">
                    <Sparkles className="w-4 h-4 text-cyan-500" />
                  </button>
                  <button type="button" className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Insert photo">
                    <Image className="w-4 h-4" />
                  </button>
                  <button type="button" className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10" title="Confidential mode">
                    <Lock className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Trash */}
              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-slate-500 hover:text-red-500 transition"
                title="Discard draft"
              >
                <Trash2 className="w-4 h-4" />
              </button>

            </div>
          </form>
        )}
      </div>
    </div>
  );
}
