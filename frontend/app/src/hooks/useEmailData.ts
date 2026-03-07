import { useState, useEffect, useCallback } from "react";
import { EmailData } from "@/components/EmailCard";

// Mock API service
const mockEmailService = {
  async fetchEmails(folder: string): Promise<EmailData[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 800));

    const allEmails: Record<string, EmailData[]> = {
      inbox: [
        {
          id: 1,
          sender: "Sarah Chen",
          avatar:
            "https://images.unsplash.com/photo-1494790108755-2616b25d0b45?w=100&h=100&fit=crop&crop=face",
          subject: "Q4 Marketing Strategy Review - Action Required",
          preview:
            "Hi team, I need your input on the Q4 marketing strategy by EOD Friday. The budget allocation needs to be finalized and I'd love to get everyone's thoughts on the proposed changes...",
          time: "2m ago",
          isStarred: false,
          isRead: false,
          hasAttachment: true,
          tags: ["work", "urgent"],
          content: `Hi team,

I hope this email finds you well.

As we approach the end of the year, it's crucial to finalize our Q4 marketing strategy. I have attached the latest draft of the strategy document for your review. Your input is vital to ensure we are aligned and ready to execute effectively.

Please pay close attention to the following sections:

• Budget Allocation: I've proposed a new allocation model based on recent performance data. Let me know your thoughts on this shift.
• Target Audience Segments: We're considering expanding into a new demographic. Feedback on the viability and potential risks is appreciated.
• Key Performance Indicators (KPIs): Are the proposed KPIs realistic and aligned with our overall business goals?

I need your input on the Q4 marketing strategy by EOD Friday. This will give us enough time to consolidate feedback and present the final plan next Monday.

Thanks for your collaboration.

Best regards,

Sarah Chen
Head of Marketing
Acme Corp`,
          attachments: [
            {
              name: "Q4_Marketing_Strategy_v3.pdf",
              size: "1.2 MB",
              type: "pdf",
            },
          ],
        },
        {
          id: 2,
          sender: "Acme Corp Notifications",
          avatar: "",
          subject: "Your monthly usage report is ready",
          preview:
            "Dear user, your detailed usage report for November is now available in your dashboard. This report includes comprehensive analytics about your email patterns, security insights, and productivity metrics...",
          time: "1h ago",
          isStarred: false,
          isRead: false,
          tags: ["work"],
          content: `Dear Jessica,

Your monthly usage report for November 2023 is now ready for review.

This comprehensive report includes:

• Email volume analysis and trends
• Security threat detection summary  
• Productivity insights and recommendations
• Storage usage and optimization tips

You can access your full report in the dashboard or download the PDF version attached.

Best regards,
Axnore Team`,
        },
        {
          id: 3,
          sender: "DevOps Team",
          avatar:
            "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
          subject: "Critical Security Alert: Server Vulnerability Detected",
          preview:
            "Immediate action required. We have detected a critical vulnerability on server cluster XYZ-01. This requires immediate patching and security review. Please coordinate with your team leads...",
          time: "3h ago",
          isStarred: true,
          isRead: false,
          content: `URGENT: Critical Security Alert

We have detected a critical vulnerability in our server infrastructure that requires immediate attention.

Details:
• Affected systems: Production cluster XYZ-01
• Vulnerability type: Remote code execution
• Risk level: CRITICAL
• Estimated patch time: 2-4 hours

Immediate action required:
1. Apply security patches during next maintenance window
2. Review access logs for suspicious activity
3. Coordinate with security team for threat assessment

Please confirm receipt and provide ETA for patch deployment.

DevOps Team
Axnore Infrastructure`,
        },
        {
          id: 4,
          sender: "Newsletter Hub",
          avatar:
            "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face",
          subject: "Weekly Digest: Latest in Tech Innovations",
          preview:
            "Discover the groundbreaking advancements in AI, blockchain, and sustainable energy this week. From OpenAI's latest announcements to breakthrough battery technology...",
          time: "Yesterday",
          isStarred: false,
          isRead: true,
          content: `This Week in Tech Innovation

Dear Tech Enthusiast,

Here are the most exciting developments in technology this week:

🤖 AI Breakthroughs
• New multimodal AI models showing remarkable reasoning capabilities
• Advances in AI safety and alignment research
• Enterprise AI adoption reaching new heights

⚡ Sustainable Technology
• Revolutionary battery technology promises 10x improvement in energy density
• Solar panel efficiency reaches record-breaking 47%
• Green hydrogen production costs dropping significantly

🔗 Blockchain & Web3
• Major financial institutions adopting blockchain for settlements
• New consensus mechanisms improving scalability
• Regulatory clarity emerging in key markets

Stay innovative!
The Newsletter Hub Team`,
        },
        {
          id: 5,
          sender: "John Doe",
          avatar:
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face",
          subject: "Lunch plans for today?",
          preview:
            "Hey Jessica! Are we still on for lunch today at 1 PM? I found this amazing new sushi place downtown that has incredible reviews. Let me know if you're still available!",
          time: "Yesterday",
          isStarred: false,
          isRead: true,
          content: `Hey Jessica!

Hope you're having a great morning! 

Are we still on for lunch today at 1 PM? I found this amazing new sushi place downtown called "Sakura Modern" that has incredible reviews. They apparently have this omakase experience that's supposed to be mind-blowing.

Let me know if you're still available - if not, we can always reschedule for later this week.

Looking forward to catching up!

John`,
        },
        {
          id: 6,
          sender: "Git Repo",
          avatar: "",
          subject: "[axnore/dashboard] New pull request #123",
          preview:
            "User 'frontend-dev' has opened a new pull request: 'feat: Improve UI responsiveness and add dark mode support'. This PR includes 47 changed files with significant improvements to mobile experience...",
          time: "2 days ago",
          isStarred: false,
          isRead: true,
          content: `Pull Request #123: feat: Improve UI responsiveness and add dark mode support

@jessica-miller A new pull request has been opened by frontend-dev

Changes include:
• Complete responsive design overhaul
• Dark mode implementation with system preference detection
• Performance optimizations for mobile devices
• Accessibility improvements (WCAG 2.1 AA compliance)
• Updated component library with modern design tokens

Files changed: 47 files (+2,847 −1,203)

This PR addresses issues #89, #134, and #156.

Please review and provide feedback.

Automated checks: ✅ All passing
Deployment preview: Available at staging-pr123.axnore.dev`,
        },
      ],
      sent: [
        {
          id: 101,
          sender: "You",
          avatar:
            "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
          subject: "Re: Project Phoenix Kick-off",
          preview:
            "Thanks for the comprehensive summary, Sarah. My action items are crystal clear and I'm excited to get started. I'll have the initial mockups ready by Thursday...",
          time: "5m ago",
          isStarred: false,
          isRead: true,
          content: `Hi Sarah,

Thanks for the comprehensive summary and clear action items from today's kick-off meeting.

I'm excited to get started on Project Phoenix! My deliverables for this week:
• Initial UI mockups by Thursday
• Technical architecture proposal by Friday
• Resource allocation recommendations

Looking forward to collaborating with the team on this exciting initiative.

Best regards,
Jessica`,
        },
        {
          id: 102,
          sender: "You",
          avatar:
            "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
          subject: "Invoice #INV-2023-1234",
          preview:
            "Hi there, please find attached the invoice for the consulting services provided during November. The total amount is $4,750 for 95 hours of development work...",
          time: "1h ago",
          isStarred: false,
          isRead: true,
          hasAttachment: true,
          content: `Dear Client Services Team,

Please find attached the invoice for consulting services provided during November 2023.

Invoice Details:
• Invoice Number: INV-2023-1234
• Period: November 1-30, 2023
• Total Hours: 95 hours
• Rate: $50/hour
• Total Amount: $4,750

Services included:
- Frontend development (React/TypeScript)
- UI/UX design improvements
- Performance optimization
- Code review and testing

Payment terms: Net 30 days
Due date: December 30, 2023

Please let me know if you have any questions.

Best regards,
Jessica Miller`,
          attachments: [
            { name: "INV-2023-1234.pdf", size: "245 KB", type: "pdf" },
          ],
        },
      ],
      archive: [
        {
          id: 201,
          sender: "HR Department",
          avatar:
            "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=100&h=100&fit=crop&crop=face",
          subject: "Company-wide Policy Update - 2023 Employee Handbook",
          preview:
            "Please review the updated employee handbook for 2023. Key changes include remote work policies, new benefits structure, and updated code of conduct guidelines...",
          time: "1 month ago",
          isStarred: false,
          isRead: true,
          hasAttachment: true,
          content: `Dear Team,

We're pleased to share the updated Employee Handbook for 2023, effective January 1st.

Key updates include:
• Enhanced remote work policies and hybrid arrangements
• Expanded health and wellness benefits
• Updated professional development opportunities
• Revised code of conduct and ethics guidelines
• New sustainability initiatives

Please review the attached handbook and confirm your acknowledgment by December 15th.

If you have any questions, please don't hesitate to reach out to HR.

Best regards,
Human Resources Team`,
          attachments: [
            { name: "Employee_Handbook_2023.pdf", size: "2.1 MB", type: "pdf" },
          ],
        },
      ],
      deleted: [
        {
          id: 301,
          sender: "Random Promotions",
          avatar: "",
          subject: "🔥 Black Friday Deals Are Here! Save up to 70%",
          preview:
            "Don't miss out on our biggest sale of the year! Incredible savings on electronics, fashion, home goods and more. Limited time offers ending soon...",
          time: "3 days ago",
          isStarred: false,
          isRead: true,
          content: `🔥 BLACK FRIDAY MEGA SALE 🔥

The biggest shopping event of the year is HERE!

Save up to 70% on:
• Electronics & Gadgets
• Fashion & Accessories  
• Home & Garden
• Sports & Fitness
• Books & Media

⏰ Limited Time: 48 hours only!
🚚 FREE shipping on orders over $50
💳 Easy returns within 30 days

Shop now before these amazing deals disappear!

[SHOP NOW] [View in Browser] [Unsubscribe]

Terms and conditions apply. Sale ends November 27th at midnight.`,
        },
      ],
    };

    return allEmails[folder] || [];
  },
};

export const useEmailData = (folder: string) => {
  const [emails, setEmails] = useState<EmailData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEmails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await mockEmailService.fetchEmails(folder);
      setEmails(data);
    } catch (err) {
      setError("Failed to fetch emails");
      console.error("Error fetching emails:", err);
    } finally {
      setLoading(false);
    }
  }, [folder]);

  useEffect(() => {
    fetchEmails();
  }, [fetchEmails]);

  const toggleStar = (emailId: number) => {
    setEmails(prevEmails =>
      prevEmails.map(email =>
        email.id === emailId ? { ...email, isStarred: !email.isStarred } : email
      )
    );
  };

  const markAsRead = (emailId: number) => {
    setEmails(prevEmails =>
      prevEmails.map(email =>
        email.id === emailId ? { ...email, isRead: true } : email
      )
    );
  };

  const deleteEmail = (emailId: number) => {
    setEmails(prevEmails => prevEmails.filter(email => email.id !== emailId));
    // In a real app, you'd make an API call to move the email to deleted folder
    // For now, we just remove it from the current view
  };

  const archiveEmail = (emailId: number) => {
    setEmails(prevEmails => prevEmails.filter(email => email.id !== emailId));
    // In a real app, you'd make an API call to move the email to archive folder
    // For now, we just remove it from the current view
  };

  return {
    emails,
    loading,
    error,
    refetch: fetchEmails,
    toggleStar,
    markAsRead,
    deleteEmail,
    archiveEmail,
  };
};
