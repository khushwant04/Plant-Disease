/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";
import React, { useState, useRef, useEffect, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Download, Upload, Mic } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

// Import shadcn/ui Select components
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";


// Base API URL - replace with environment variable in production
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
    from: "user" | "bot";
    text: string;
    loading?: boolean;
}

// --- Translations Object ---
// Add translations for Indian languages (Kannada, Tamil, Hindi)
// Note: The actual diagnosis content from the AI (disease name, details) *should now*
// be in the selected language, but the original *prediction* like "class_name" is still
// based on the English model label. The prompt asks Gemini to elaborate *on* that English label
// in the target language.
const translations: { [key: string]: any } = {
    en: {
        selectLanguage: "Select Language",
        initialMessage: "🌿 Upload an image of the plant to get a diagnosis.",
        uploadedImage: "📸 Uploaded image:",
        thinking: "Thinking...",
        analysisFailed: "Analysis failed. Please try again.",
        analysisFailedStatus: (status: number) => `Analysis failed with status: ${status}`,
        analysisFailedError: (err: string) => `❌ ${err}`,
        healthyPlant: "✅ The plant appears to be healthy.",
        predictionLabel: "Prediction",
        confidenceLabel: "Confidence",
        analysisLabel: "Analysis",
        pdfDownloaded: "✅ Your plant diagnosis report has been downloaded.",
        pdfFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'Failed to generate PDF. Please try again.'}`,
        newDiagnosisButton: "New Diagnosis",
        generateReportButton: "Generate Report",
        generatingReport: "Generating...",
        uploadButton: "Upload Plant Image",
        uploadingButton: "Analyzing...",
        uploadHint: "Upload a clear image of the plant leaves or affected areas",
        inputPlaceholder: "Ask about the diagnosis...",
        sendButton: "Send",
        streamFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'Failed to get response. Please try again.'}`,
        contentDisclaimer: "Note: While the main analysis is in your chosen language, disease names might appear in English.",
        // Add this new disclaimer or modify the existing one
    },
    hi: { // Hindi
        selectLanguage: "भाषा चुनें",
        initialMessage: "🌿 पौधे की पहचान के लिए एक तस्वीर अपलोड करें।",
        uploadedImage: "📸 अपलोड की गई तस्वीर:",
        thinking: "सोच रहा है...",
        analysisFailed: "विश्लेषण विफल हुआ। कृपया पुनः प्रयास करें।",
        analysisFailedStatus: (status: number) => `स्थिति ${status} के साथ विश्लेषण विफल हुआ।`,
        analysisFailedError: (err: string) => `❌ ${err}`,
        healthyPlant: "✅ पौधा स्वस्थ दिख रहा है।",
        predictionLabel: "भविष्यवाणी",
        confidenceLabel: "आत्मविश्वास",
        analysisLabel: "विश्लेषण",
        pdfDownloaded: "✅ आपकी पौधा रोग निदान रिपोर्ट डाउनलोड हो गई है।",
        pdfFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'प्रतिक्रिया प्राप्त करने में विफल रहा। कृपया पुनः प्रयास करें।'}`,
        newDiagnosisButton: "नया निदान",
        generateReportButton: "रिपोर्ट जनरेट करें",
        generatingReport: "जनरेट हो रहा है...",
        uploadButton: "पौधे की तस्वीर अपलोड करें",
        uploadingButton: "विश्लेषण हो रहा है...",
        uploadHint: "पत्ती या प्रभावित क्षेत्र की स्पष्ट तस्वीर अपलोड करें",
        inputPlaceholder: "निदान के बारे में पूछें...",
        sendButton: "भेजें",
        streamFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'प्रतिक्रिया प्राप्त करने में विफल रहा। कृपया पुनः प्रयास करें।'}`,
        contentDisclaimer: "ध्यान दें: मुख्य विश्लेषण आपकी चुनी हुई भाषा में है, लेकिन रोग के नाम अंग्रेजी में दिखाई दे सकते हैं।",
    },
    kn: { // Kannada (Translated using Google Translate, verify with native speaker if possible)
        selectLanguage: "ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ",
        initialMessage: "🌿 ಸಸ್ಯದ ರೋಗನಿರ್ಣಯಕ್ಕಾಗಿ ಚಿತ್ರವನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ.",
        uploadedImage: "📸 ಅಪ್ಲೋಡ್ ಮಾಡಿದ ಚಿತ್ರ:",
        thinking: "ಆಲೋಚಿಸುತ್ತಿದೆ...",
        analysisFailed: "ವಿಶ್ಲೇಷಣೆ ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
        analysisFailedStatus: (status: number) => `ಸ್ಥಿತಿ ${status} ಯೊಂದಿಗೆ ವಿಶ್ಲೇಷಣೆ ವಿಫಲವಾಗಿದೆ.`,
        analysisFailedError: (err: string) => `❌ ${err}`,
        healthyPlant: "✅ ಸಸ್ಯವು ಆರೋಗ್ಯಕರವಾಗಿ ಕಾಣುತ್ತದೆ.",
        predictionLabel: "ಮುನ್ಸೂಚನೆ",
        confidenceLabel: "ವಿಶ್ವಾಸಾರ್ಹತೆ",
        analysisLabel: "ವಿಶ್ಲೇಷಣೆ",
        pdfDownloaded: "✅ ನಿಮ್ಮ ಸಸ್ಯ ರೋಗನಿರ್ಣಯ ವರದಿಯನ್ನು ಡೌನ್ಲೋಡ್ ಮಾಡಲಾಗಿದೆ.",
        pdfFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ಪಡೆಯಲು ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'}`,
        newDiagnosisButton: "ಹೊಸ ರೋಗನಿರ್ಣಯ",
        generateReportButton: "ವರದಿಯನ್ನು ರಚಿಸಿ",
        generatingReport: "ರಚಿಸಲಾಗುತ್ತಿದೆ...",
        uploadButton: "ಸಸ್ಯದ ಚಿತ್ರವನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ",
        uploadingButton: "ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
        uploadHint: "ಸಸ್ಯದ ಎಲೆಗಳು ಅಥವಾ ಬಾಧಿತ ಪ್ರದೇಶಗಳ ಸ್ಪಷ್ಟ ಚಿತ್ರವನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಿ",
        inputPlaceholder: "ರೋಗನಿರ್ಣಯದ ಬಗ್ಗೆ ಕೇಳಿ...",
        sendButton: "ಕಳುಹಿಸಿ",
        streamFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ಪಡೆಯಲು ವಿಫಲವಾಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'}`,
        contentDisclaimer: "ಸೂಚನೆ: ಮುಖ್ಯ ವಿಶ್ಲೇಷಣೆ ನಿಮ್ಮ ಆಯ್ದ ಭಾಷೆಯಲ್ಲಿದ್ದರೂ, ರೋಗದ ಹೆಸರುಗಳು ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಕಾಣಿಸಿಕೊಳ್ಳಬಹುದು.",
    },
    ta: { // Tamil (Translated using Google Translate, verify with native speaker if possible)
        selectLanguage: "மொழியைத் தேர்ந்தெடுக்கவும்",
        initialMessage: "🌿 தாவரத்தின் நோயறிதலுக்காக ஒரு படத்தைப் பதிவேற்றவும்.",
        uploadedImage: "📸 பதிவேற்றப்பட்ட படம்:",
        thinking: "யோசிக்கிறது...",
        analysisFailed: "பகுப்பாய்வு தோல்வியடைந்தது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
        analysisFailedStatus: (status: number) => `நிலை ${status} உடன் பகுப்பாய்வு தோல்வியடைந்தது.`,
        analysisFailedError: (err: string) => `❌ ${err}`,
        healthyPlant: "✅ தாவரம் ஆரோக்கியமாகத் தெரிகிறது.",
        predictionLabel: "முன்னறிவிப்பு",
        confidenceLabel: "நம்பிக்கை",
        analysisLabel: "பகுப்பாய்வு",
        pdfDownloaded: "✅ உங்கள் தாவர நோயறிதல் அறிக்கை பதிவிறக்கம் செய்யப்பட்டுள்ளது.",
        pdfFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'பதிலைப் பெறத் தவறிவிட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.'}`,
        newDiagnosisButton: "புதிய நோயறிதல்",
        generateReportButton: "அறிக்கையை உருவாக்கவும்",
        generatingReport: "உருவாக்கப்படுகிறது...",
        uploadButton: "தாவரப் படத்தைப் பதிவேற்றவும்",
        uploadingButton: "பகுப்பாய்வு செய்கிறது...",
        uploadHint: "தாவர இலைகள் அல்லது பாதிக்கப்பட்ட பகுதிகளின் தெளிவான படத்தைப் பதிவேற்றவும்",
        inputPlaceholder: "நோயறிதலைப் பற்றி கேளுங்கள்...",
        sendButton: "அனுப்பு",
        streamFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'பதிலைப் பெறத் தவறிவிட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.'}`,
        contentDisclaimer: "குறிப்பு: முக்கிய பகுப்பாய்வு நீங்கள் தேர்ந்தெடுத்த மொழியில் இருந்தாலும், நோய்களின் பெயர்கள் ஆங்கிலத்தில் தோன்றக்கூடும்.",
    },
    // Add more languages as needed
    ml: { // Malayalam (Using Google Translate)
        selectLanguage: "ഭാഷ തിരഞ്ഞെടുക്കുക",
        initialMessage: "🌿 രോഗനിർണ്ണയത്തിനായി ചെടിയുടെ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക.",
        uploadedImage: "📸 അപ്‌ലോഡ് ചെയ്ത ചിത്രം:",
        thinking: "ചിന്തിക്കുന്നു...",
        analysisFailed: "വിശകലനം പരാജയപ്പെട്ടു. ദയവായി വീണ്ടും ശ്രമിക്കുക.",
        analysisFailedStatus: (status: number) => `സ്റ്റാറ്റസ് ${status} ഉപയോഗിച്ച് വിശകലനം പരാജയപ്പെട്ടു.`,
        analysisFailedError: (err: string) => `❌ ${err}`,
        healthyPlant: "✅ ചെടി ആരോഗ്യകരമായി കാണപ്പെടുന്നു.",
        predictionLabel: "പ്രവചനം",
        confidenceLabel: "വിശ്വാസ്യത",
        analysisLabel: "വിശകലനം",
        pdfDownloaded: "✅ നിങ്ങളുടെ ചെടി രോഗനിർണ്ണയ റിപ്പോർട്ട് ഡൗൺലോഡ് ചെയ്തു.",
        pdfFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'പ്രതികരണം ലഭിക്കാൻ പരാജയപ്പെട്ടു. ദയവായി വീണ്ടും ശ്രമിക്കുക.'}`,
        newDiagnosisButton: "പുതിയ രോഗനിർണ്ണയം",
        generateReportButton: "റിപ്പോർട്ട് ഉണ്ടാക്കുക",
        generatingReport: "ഉണ്ടാക്കുന്നു...",
        uploadButton: "ചെടിയുടെ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക",
        uploadingButton: "വിശകലനം ചെയ്യുന്നു...",
        uploadHint: "ചെടിയുടെ ഇലകളുടെയോ ബാധിച്ച ഭാഗങ്ങളുടെയോ വ്യക്തമായ ചിത്രം അപ്‌ലോഡ് ചെയ്യുക",
        inputPlaceholder: "രോഗനിർണ്ണയത്തെക്കുറിച്ച് ചോദിക്കുക...",
        sendButton: "അയക്കുക",
        streamFailed: (err: string) => `❌ ${err instanceof Error ? err.message : 'പ്രതികരണം ലഭിക്കാൻ പരാജയപ്പെട്ടു. ദയവായി വീണ്ടും ശ്രമിക്കുക.'}`,
        contentDisclaimer: "ശ്രദ്ധിക്കുക: പ്രധാന വിശകലനം നിങ്ങൾ തിരഞ്ഞെടുത്ത ഭാഷയിലാണെങ്കിലും, രോഗങ്ങളുടെ പേരുകൾ ഇംഗ്ലീഷിൽ കാണാം.",
    },
    // ... add other languages
};

// Map language codes to display names
const languageOptions = {
    en: "English",
    hi: "हिंदी (Hindi)",
    kn: "ಕನ್ನಡ (Kannada)",
    ta: "தமிழ் (Tamil)",
    ml: "മലയാളം (Malayalam)",
    // Add display names for other languages here
};


const SideChatBot: React.FC = () => {
    // Initialize with English or get from localStorage/context if you want persistence
    const [currentLang, setCurrentLang] = useState('en');
    const t = useMemo(() => translations[currentLang] || translations.en, [currentLang]);

    // Update initial message based on current language state
    const [messages, setMessages] = useState<Message[]>(() => [
        { from: "bot", text: translations[currentLang]?.initialMessage || translations.en.initialMessage }
    ]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [chatEnabled, setChatEnabled] = useState(false);
    const [diagnosisContext, setDiagnosisContext] = useState(""); // Still store context in English for backend query base
    const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
    const scrollAreaRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll to bottom of chat
    useEffect(() => {
        const scrollContainer = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]');
        if (scrollContainer) {
            scrollContainer.scrollTo({ top: scrollContainer.scrollHeight, behavior: 'smooth' });
        }
    }, [messages]);

    // Effect to update the initial message and potentially the last bot message when language changes
    useEffect(() => {
        // Update initial message if chat hasn't started
        if (!chatEnabled && messages.length === 1 && messages[0].from === 'bot') {
            setMessages([{ from: "bot", text: t.initialMessage }]);
        } else if (messages.length > 0 && messages[messages.length - 1].from === 'bot') {
            // Attempt to update the text of the last bot message if it's one of the known static ones
            const lastMessage = messages[messages.length - 1];
            let updatedText = lastMessage.text;

            // Check if it's the PDF downloaded message and update its translation
            const pdfDownloadedEnglish = translations.en.pdfDownloaded;
            const isPdfDownloaded = Object.values(translations).some(langTrans =>
                lastMessage.text.includes(langTrans.pdfDownloaded)
            );
            if (isPdfDownloaded) {
                updatedText = t.pdfDownloaded;
            }
            // You could add similar checks for other static bot messages if needed,
            // but most bot messages will be dynamic AI output now.

            if (updatedText !== lastMessage.text) {
                setMessages(prev => {
                    const updated = [...prev];
                    updated[updated.length - 1] = { ...lastMessage, text: updatedText };
                    return updated;
                });
            }
        }
    }, [currentLang, chatEnabled]); // Depend on currentLang and chatEnabled


    // Handle language change
    const handleLanguageChange = (lang: string) => {
        setCurrentLang(lang);
        // Reset messages to the initial state in the new language if no diagnosis is in progress
        if (!chatEnabled) {
            setMessages([{ from: "bot", text: translations[lang]?.initialMessage || translations.en.initialMessage }]);
        }
    };


    // Handle image analysis
    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setMessages(prev => [...prev,
        { from: "user", text: `${t.uploadedImage} ${file.name}` },
        { from: "bot", text: "", loading: true }
        ]);

        const formData = new FormData();
        formData.append("file", file);
        formData.append("language", currentLang); // *** Send the language code ***

        try {
            const res = await fetch(`${API_BASE_URL}/analyze/`, {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                let errorDetail = `status: ${res.status}`;
                try {
                    const errorJson = await res.json();
                    if (errorJson.error) {
                        errorDetail = errorJson.error;
                    }
                } catch (e) {
                    // Ignore JSON parsing errors, use status
                }
                throw new Error(errorDetail);
            }

            const data = await res.json();

            // The prediction part still uses the original English class name from the model
            // The gemini_response should be in the target language
            const predictionText = data.prediction.class_index !== null
                ? `**${t.predictionLabel}**: ${data.prediction.class_name} (${t.predictionLabel})\n**${t.confidenceLabel}**: ${(data.prediction.confidence * 100).toFixed(2)}%`
                : t.healthyPlant; // Use translated text for healthy plant

            // data.gemini_response should now be in the target language
            const responseText = `${predictionText}\n\n**${t.analysisLabel}**:\n${data.gemini_response}\n\n---\n*${t.contentDisclaimer}*`; // Add disclaimer

            // Store the original English diagnosis context for follow-up questions if needed
            // Or, store the generated text in the target language?
            // Let's store the English context for the backend prompt structure for now.
            // A more advanced approach might involve translating the user's question
            // on the backend and using that with the original English context.
            // For this implementation, we assume the backend takes the English context
            // and the user's question (potentially in local language) and generates
            // the *response* in the selected language.
            setDiagnosisContext(data.gemini_response); // Storing the generated text as context

            setChatEnabled(true);

            setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { from: "bot", text: responseText };
                return updated;
            });
        } catch (err) {
            console.error(err);
            setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                    from: "bot",
                    text: t.analysisFailedError(err instanceof Error ? err.message : t.analysisFailed)
                };
                return updated;
            });
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    // Handle follow-up Q&A
    const handleSend = async (e?: React.FormEvent) => {
        if (e) {
            e.preventDefault();
        }

        if (!input.trim() || isStreaming) return;

        const question = input; // User input can be in any language
        const currentContext = diagnosisContext; // Get the last generated bot response as context
        setInput("");
        setMessages(prev => [...prev,
        { from: "user", text: question },
        { from: "bot", text: "", loading: true }
        ]);
        setIsStreaming(true);

        try {
            // Send the user's question and the last bot response (as context) to the backend
            // along with the preferred response language.
            const res = await fetch(`${API_BASE_URL}/generate-stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // Send the last generated bot response (as context), the user's question, and the language
                body: JSON.stringify({
                    // This combined input will be sent to the backend endpoint
                    // The backend will then add the language instruction to this input before sending to Gemini
                    // We're passing the *last bot response* as context here. If the backend
                    // relied strictly on the *original diagnosis context* (which was English),
                    // you'd pass that instead. Using the last response *might* help Gemini
                    // stay in the current conversation's language context better.
                    input: `Previous diagnosis/response context: "${currentContext}". User asks: "${question}"`,
                    language: currentLang // *** Send the language code ***
                })
            });

            if (!res.ok) {
                // If the initial request fails before streaming starts
                let errorDetail = `status: ${res.status}`;
                try {
                    const errorJson = await res.json();
                    if (errorJson.error) {
                        errorDetail = errorJson.error;
                    }
                } catch (e) {
                    // Ignore JSON parsing errors
                }
                throw new Error(errorDetail);
            }

            const reader = res.body?.getReader();
            const decoder = new TextDecoder("utf-8");
            if (!reader) throw new Error("Failed to create reader");

            setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { from: "bot", text: "" }; // Prepare for streaming text
                return updated;
            });

            let receivedText = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                receivedText += chunk; // Accumulate text to potentially update context later
                setMessages(prev => {
                    const updated = [...prev];
                    // Append the chunk to the last message's text
                    updated[updated.length - 1] = {
                        from: "bot",
                        text: updated[updated.length - 1].text + chunk
                    };
                    return updated;
                });
            }
            // Update diagnosisContext with the full received response for future follow-ups
            setDiagnosisContext(receivedText);

        } catch (err) {
            console.error(err);
            setMessages(prev => {
                const updated = [...prev];
                // If loading was still true, replace it with the error message
                if (updated.length > 0 && updated[updated.length - 1].loading) {
                    updated[updated.length - 1] = {
                        from: "bot",
                        text: t.streamFailed(err) // Use translated stream failed message
                    };
                } else {
                    // Or add a new error message if stream failed after some content
                    updated.push({ from: "bot", text: t.streamFailed(err) });
                }
                return updated;
            });
        } finally {
            setIsStreaming(false);
        }
    };

    // Download PDF report (No changes needed here, it sends the current messages which *should*
    // Download PDF report - Corrected to send the expected JSON structure
    const handleDownloadPdf = async () => {
        try {
            setIsGeneratingPDF(true);

            const res = await fetch(`${API_BASE_URL}/generate-pdf/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // Corrected body: Wrap messages in an object and add language
                body: JSON.stringify({
                    messages: messages, // <-- Send the array under the 'messages' key
                    language: currentLang // <-- Send the language under the 'language' key
                })
            });

            if (!res.ok) {
                let errorMessage = `PDF generation failed with status: ${res.status}`;
                try {
                    // Try to parse error details if available (FastAPI sends JSON for 422)
                    const errorData = await res.json();
                    if (errorData.detail) { // FastAPI 422 errors often use 'detail'
                        errorMessage = `PDF generation failed: ${JSON.stringify(errorData.detail)}`;
                    } else if (errorData.error) { // Custom error format
                        errorMessage = errorData.error;
                    }
                } catch (e) { /* ignore JSON parse errors */ }
                throw new Error(errorMessage);
            }

            const contentType = res.headers.get('content-type');
            if (!contentType || !contentType.includes('application/pdf')) {
                // If response is OK but not PDF, try to read it as text/JSON for more info
                let responseText = await res.text();
                try {
                    const responseJson = JSON.parse(responseText);
                    if (responseJson.error) responseText = responseJson.error;
                } catch (e) { /* ignore parse error */ }
                throw new Error(`Server did not return a valid PDF file. Response: ${responseText}`);
            }


            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "PlantAI_Report.pdf";
            a.click();
            window.URL.revokeObjectURL(url);

            setMessages(prev => [...prev,
            { from: "bot", text: t.pdfDownloaded }
            ]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev,
            { from: "bot", text: t.pdfFailed(err) }
            ]);
        } finally {
            setIsGeneratingPDF(false);
        }
    };

    // For handling new image upload after a diagnosis
    const handleRestart = () => {
        setChatEnabled(false);
        setDiagnosisContext("");
        setMessages([
            { from: "bot", text: t.initialMessage } // Use translated initial message
        ]);
    };

    // Custom markdown components (remain style-related, no translation needed here)
    const MarkdownComponents = {
        h1: (props: any) => <h1 className="text-2xl font-bold my-4" {...props} />,
        h2: (props: any) => <h2 className="text-xl font-bold my-3" {...props} />,
        h3: (props: any) => <h3 className="text-lg font-bold my-2" {...props} />,
        ul: (props: any) => <ul className="list-disc ml-6 my-2" {...props} />,
        ol: (props: any) => <ol className="list-decimal ml-6 my-2" {...props} />,
        code: (props: any) => {
            const { children, className } = props;
            return className ? (
                <pre className="bg-gray-800 text-white p-2 rounded my-2 overflow-x-auto">
                    <code className={className}>{children}</code>
                </pre>
            ) : (
                <code className="bg-gray-200 px-1 rounded">{children}</code>
            );
        },
        blockquote: (props: any) => <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2" {...props} />,
        a: (props: any) => <a className="text-blue-500 hover:underline" {...props} />,
        p: (props: any) => <p className="my-2" {...props} />,
    };


    return (
        <div className="w-[400px] h-screen text-gray-900 bg-white flex flex-col">
            <div className="p-4 text-lg font-semibold border-b flex justify-between items-center bg-green-700 text-white">
                <span>🌿 PlantAI Assistant</span>
                {/* Language Selector */}
                {/* Place this higher up if you want language selection always visible */}
                {/* Or keep it here, but maybe adjust flex layout */}
                <div className="flex items-center gap-2">
                    {chatEnabled && (
                        <Button onClick={handleRestart} variant="outline" size="sm" className="text-xs bg-white text-green-700 hover:bg-gray-100 h-8"> {/* Added h-8 for better alignment */}
                            {t.newDiagnosisButton}
                        </Button>
                    )}
                    <Select onValueChange={handleLanguageChange} value={currentLang}>
                        <SelectTrigger className="w-[140px] text-sm bg-white text-green-700 border-green-700 hover:bg-gray-100 h-8"> {/* Added h-8 */}
                            <SelectValue placeholder={t.selectLanguage} />
                        </SelectTrigger>
                        <SelectContent>
                            {Object.keys(languageOptions).map((langKey) => (
                                <SelectItem key={langKey} value={langKey}>
                                    {languageOptions[langKey as keyof typeof languageOptions]}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <ScrollArea ref={scrollAreaRef} className="flex-1 p-2 space-y-2 overflow-hidden">
                {messages.map((msg, i) => (
                    <div
                        key={i}
                        className={`p-3 m-2 rounded-xl max-w-[90%] ${msg.from === "bot"
                            ? "bg-gray-100 text-left ml-0 mr-auto"
                            : "bg-green-100 text-black text-left ml-auto mr-0"
                            }`}>
                        {msg.loading ? (
                            <div className="flex items-center gap-2">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                <span>{t.thinking}</span>
                            </div>
                        ) : msg.from === "bot" ? (
                            <ReactMarkdown
                                components={MarkdownComponents}
                                remarkPlugins={[remarkGfm]}
                                rehypePlugins={[rehypeRaw, rehypeSanitize]}
                            >
                                {msg.text}
                            </ReactMarkdown>
                        ) : (
                            <div className="whitespace-pre-wrap">{msg.text}</div>
                        )}
                    </div>
                ))}
            </ScrollArea>

            {/* Generate Report button after diagnosis */}
            {chatEnabled && (
                <div className="p-2 border-t flex justify-center">
                    <Button
                        onClick={handleDownloadPdf}
                        disabled={isGeneratingPDF || isStreaming}
                        className="bg-green-700 hover:bg-green-800 w-full" // Make button full width
                    >
                        {isGeneratingPDF ? (
                            <>
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" /> {t.generatingReport}
                            </>
                        ) : (
                            <>
                                <Download className="h-4 w-4 mr-2" /> {t.generateReportButton}
                            </>
                        )}
                    </Button>
                </div>
            )}

            {/* Image upload or chat input */}
            {!chatEnabled ? (
                <div className="p-4 border-t border-gray-300">
                    <div className="flex flex-col gap-2">
                        <div className="flex flex-row p-4 space-x-2">
                            <Button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isUploading}
                                className="bg-green-700 hover:bg-green-800 w-full" // Make button full width
                            >
                                {isUploading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" /> {t.uploadingButton}
                                    </>
                                ) : (
                                    <>
                                        <Upload className="h-4 w-4 mr-2" /> {t.uploadButton}
                                    </>
                                )}
                            </Button>
                            <Button>
                                <Mic/>
                            </Button>
                       </div>
                        <Input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleImageUpload}
                            className="hidden"
                            disabled={isUploading}
                        />
                        <p className="text-xs text-gray-500 text-center">
                            {t.uploadHint}
                        </p>
                    </div>
                </div>
            ) : (
                <form
                    onSubmit={handleSend}
                    className="p-4 border-t border-gray-300 flex gap-2"
                >
                    <Input
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        className="flex-1 bg-white text-gray-900"
                        placeholder={t.inputPlaceholder}
                        disabled={isStreaming}
                    />
                    <Button
                        type="submit"
                        disabled={isStreaming || !input.trim()}
                        className="bg-green-700 hover:bg-green-800"
                    >
                        {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : "Send"}
                    </Button>
                </form>
            )}
        </div>
    );
};

export default SideChatBot;