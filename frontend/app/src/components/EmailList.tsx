import React, { useState } from "react";
import { Loader2, RefreshCw, AlertCircle } from "lucide-react";
import EmailCard, { EmailData } from "./EmailCard";
import { useEmailData } from "@/hooks/useEmailData";

interface EmailListProps {
  folder: string;
  searchQuery?: string;
  tagFilter?: string | null;
  onReply?: (email: EmailData) => void;
  onForward?: (email: EmailData) => void;
  onAutoWrite?: (email: EmailData) => void;
}

const EmailList: React.FC<EmailListProps> = ({
  folder,
  searchQuery,
  tagFilter = null,
  onReply,
  onForward,
  onAutoWrite,
}) => {
  const {
    emails,
    loading,
    error,
    refetch,
    toggleStar,
    markAsRead,
    deleteEmail,
    archiveEmail,
  } = useEmailData(folder);
  const [openEmailId, setOpenEmailId] = useState<number | null>(null);

  const handleEmailToggle = (emailId: number) => {
    if (openEmailId === emailId) {
      setOpenEmailId(null);
    } else {
      setOpenEmailId(emailId);
      markAsRead(emailId);
    }
  };

  const handleToggleStar = (emailId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    toggleStar(emailId);
  };

  const handleUpdateTags = (emailId: number, newTags: string[]) => {
    // Update the local state to reflect the tag changes
    const updatedEmails = emails.map(email =>
      email.id === emailId ? { ...email, tags: newTags } : email
    );
    // Note: In a real app, you'd also make an API call to persist the changes
    // For now, we'll just update the local state
    // You might want to add this to your useEmailData hook
    console.log(`Updated tags for email ${emailId}:`, newTags);
  };

  const handleDelete = (emailId: number) => {
    deleteEmail(emailId);
    if (openEmailId === emailId) {
      setOpenEmailId(null);
    }
  };

  const handleArchive = (emailId: number) => {
    archiveEmail(emailId);
    if (openEmailId === emailId) {
      setOpenEmailId(null);
    }
  };

  // Filter emails based on search query and tag filter
  const filteredEmails = emails.filter(email => {
    const matchesSearch = searchQuery
      ? email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
        email.sender.toLowerCase().includes(searchQuery.toLowerCase()) ||
        email.preview.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    // If tagFilter is set,
    const matchesTag =
      tagFilter && tagFilter !== "all" ? email.tags?.includes(tagFilter) : true;
    return matchesSearch && matchesTag;
  });

  // Ensure "All" tag button is always shown by not hiding it even if no emails match the current tag filter

  const getFolderTitle = () => {
    if (folder === "inbox") return "";
    const titles: Record<string, string> = {
      sent: "Sent Messages",
      archive: "Archived Emails",
      deleted: "Deleted Messages",
    };
    const baseTitle = titles[folder] || "Emails";
    if ((searchQuery || tagFilter) && filteredEmails.length !== emails.length) {
      return `${baseTitle} (${filteredEmails.length} results)`;
    }
    return baseTitle;
  };

  const getEmptyMessage = () => {
    const messages: Record<string, string> = {
      inbox: "No new emails in your inbox",
      sent: "No sent messages to display",
      archive: "No archived emails found",
      deleted: "Trash is empty",
    };
    return messages[folder] || "No emails found";
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-8 space-y-3">
        <Loader2 className="w-6 h-6 text-accent-primary animate-spin" />
        <p className="text-xs text-text-secondary">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 space-y-4">
        <AlertCircle className="w-8 h-8 text-danger-text" />
        <p className="text-sm text-danger-text font-medium">{error}</p>
        <button
          onClick={refetch}
          className="flex items-center px-4 py-2 text-sm font-medium text-accent-text bg-accent-primary rounded-lg hover:bg-accent-primary-hover transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </button>
      </div>
    );
  }

  if (filteredEmails.length === 0) {
    return (
      <div className="py-16 space-y-4">
        <div className="flex flex-col items-center justify-center space-y-4 mb-4">
          <div className="w-16 h-16 bg-bg-tertiary rounded-full flex items-center justify-center">
            <span className="text-2xl text-text-tertiary">📭</span>
          </div>
          <p className="text-sm text-text-secondary font-medium text-center">
            {searchQuery || tagFilter
              ? `No emails found matching your criteria`
              : getEmptyMessage()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      {getFolderTitle() && (
        <div className="flex flex-col space-y-3 mb-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-text-primary">
              {getFolderTitle()}
            </h3>
          </div>
        </div>
      )}

      {/* Email Cards */}
      <div className="space-y-3">
        {filteredEmails.map(email => (
          <EmailCard
            key={email.id}
            email={email}
            isOpen={openEmailId === email.id}
            onToggle={() => handleEmailToggle(email.id)}
            onToggleStar={e => handleToggleStar(email.id, e)}
            onUpdateTags={handleUpdateTags}
            onDelete={handleDelete}
            onArchive={handleArchive}
            onReply={onReply}
            onForward={onForward}
            onAutoWrite={onAutoWrite}
          />
        ))}
      </div>
    </div>
  );
};

export default EmailList;
