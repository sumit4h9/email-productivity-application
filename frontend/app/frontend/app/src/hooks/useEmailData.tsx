import { useState, useEffect, useCallback } from "react";

// Mock email data interface
export interface EmailData {
  id: number;
  sender: {
    name: string;
    email: string;
    avatar?: string;
  };
  subject: string;
  preview: string;
  content: string;
  date: string;
  isRead: boolean;
  isStarred: boolean;
  labels?: string[];
  attachments?: {
    name: string;
    size: string;
    type: string;
  }[];
}

// Mock data
const mockEmails: Record<string, EmailData[]> = {
  inbox: [
    {
      id: 1,
      sender: {
        name: "Alice Johnson",
        email: "alice@company.com",
        avatar:
          "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face",
      },
      subject: "Weekly Team Update",
      preview: "Here's a summary of what our team accomplished this week...",
      content: `Hi team,

Here's a summary of what our team accomplished this week:

- Completed the new feature implementation
- Fixed 3 critical bugs
- Improved test coverage by 15%
- Held successful client demo

Great work everyone!

Best regards,
Alice`,
      date: "2023-09-08T10:30:00",
      isRead: false,
      isStarred: true,
      labels: ["Team", "Important"],
    },
    {
      id: 2,
      sender: {
        name: "Marketing Team",
        email: "marketing@company.com",
        avatar:
          "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop&crop=face",
      },
      subject: "Q4 Marketing Strategy Review",
      preview: "Please review the attached Q4 marketing strategy document...",
      content: `Hello everyone,

Please review the attached Q4 marketing strategy document before our meeting next week. Key points to focus on:

1. Social media campaign plans
2. Budget allocation
3. KPI targets

Thanks,
Marketing Team`,
      date: "2023-09-08T09:15:00",
      isRead: false,
      isStarred: false,
      labels: ["Marketing", "Review"],
      attachments: [
        {
          name: "Q4_Marketing_Strategy.pdf",
          size: "2.4 MB",
          type: "pdf",
        },
      ],
    },
    {
      id: 3,
      sender: {
        name: "HR Department",
        email: "hr@company.com",
        avatar:
          "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop&crop=face",
      },
      subject: "Important: Company Policy Update",
      preview: "Please review the updated company policies...",
      content: `Dear employees,

This is a notification about recent updates to our company policies. Please review the attached documents carefully.

Key changes include:
- Remote work guidelines
- Vacation policy updates
- New health benefits

Please acknowledge receipt by EOD.

Best regards,
HR Team`,
      date: "2023-09-07T16:45:00",
      isRead: true,
      isStarred: true,
      labels: ["HR", "Important"],
      attachments: [
        {
          name: "Company_Policies_2023.pdf",
          size: "1.8 MB",
          type: "pdf",
        },
      ],
    },
  ],
  sent: [
    {
      id: 4,
      sender: {
        name: "You",
        email: "you@company.com",
      },
      subject: "Re: Project Timeline",
      preview: "I've reviewed the timeline and here are my thoughts...",
      content: "I've reviewed the timeline and here are my thoughts...",
      date: "2023-09-08T11:00:00",
      isRead: true,
      isStarred: false,
    },
  ],
  archive: [],
  deleted: [],
};

export const useEmailData = (folder: string) => {
  const [emails, setEmails] = useState<EmailData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEmails = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call with reduced delay (500ms instead of typical 2-3s)
      await new Promise(resolve => setTimeout(resolve, 500));

      // Get mock data for the folder
      const folderEmails = mockEmails[folder] || [];
      setEmails(folderEmails);
    } catch (err) {
      setError("Failed to fetch emails. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [folder]);

  useEffect(() => {
    fetchEmails();
  }, [fetchEmails]);

  const toggleStar = (emailId: number) => {
    setEmails(
      emails.map(email =>
        email.id === emailId ? { ...email, isStarred: !email.isStarred } : email
      )
    );
  };

  const markAsRead = (emailId: number) => {
    setEmails(
      emails.map(email =>
        email.id === emailId ? { ...email, isRead: true } : email
      )
    );
  };

  return {
    emails,
    loading,
    error,
    refetch: fetchEmails,
    toggleStar,
    markAsRead,
  };
};
