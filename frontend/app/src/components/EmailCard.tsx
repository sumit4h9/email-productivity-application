import React, { useState } from "react";
import {
  Star,
  StarOff,
  FileText,
  Bell,
  Code,
  Megaphone,
  Download,
  Eye,
  Reply,
  ReplyAll,
  Forward,
  Edit3,
  X,
  Plus,
  Check,
  Tag,
  Trash2,
  Archive,
  Sparkles,
} from "lucide-react";

export interface EmailData {
  id: number;
  sender: string;
  avatar: string;
  subject: string;
  preview: string;
  time: string;
  isStarred: boolean;
  isRead: boolean;
  hasAttachment?: boolean;
  content?: string;
  attachments?: Array<{
    name: string;
    size: string;
    type: string;
  }>;
  tags?: string[];
}

interface EmailCardProps {
  email: EmailData;
  isOpen: boolean;
  onToggle: () => void;
  onToggleStar: (e: React.MouseEvent) => void;
  onUpdateTags?: (emailId: number, tags: string[]) => void;
  onDelete?: (emailId: number) => void;
  onArchive?: (emailId: number) => void;
  onReply?: (email: EmailData) => void;
  onForward?: (email: EmailData) => void;
  onAutoWrite?: (email: EmailData) => void;
}

const EmailCard: React.FC<EmailCardProps> = ({
  email,
  isOpen,
  onToggle,
  onToggleStar,
  onUpdateTags,
  onDelete,
  onArchive,
  onReply,
  onForward,
  onAutoWrite,
}) => {
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [editingTags, setEditingTags] = useState<string[]>(email.tags || []);
  const [newTagInput, setNewTagInput] = useState("");

  const getEmailIcon = (sender: string) => {
    if (sender.includes("Notifications"))
      return <Bell className="text-purple-600 text-lg" />;
    if (sender.includes("Git"))
      return <Code className="text-blue-600 text-lg" />;
    if (sender.includes("Promotions"))
      return <Megaphone className="text-red-600 text-lg" />;
    return null;
  };

  const handleAddTag = () => {
    if (newTagInput.trim() && !editingTags.includes(newTagInput.trim())) {
      setEditingTags([...editingTags, newTagInput.trim()]);
      setNewTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setEditingTags(editingTags.filter(tag => tag !== tagToRemove));
  };

  const handleSaveTags = () => {
    if (onUpdateTags) {
      onUpdateTags(email.id, editingTags);
    }
    setIsEditingTags(false);
  };

  const handleCancelEdit = () => {
    setEditingTags(email.tags || []);
    setNewTagInput("");
    setIsEditingTags(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleAddTag();
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  const renderEmailContent = () => {
    if (!email.content) return null;

    return (
      <div className="overflow-hidden transition-all duration-300 ease-out">
        <div className="border-t border-border-primary">
          <div className="p-6 leading-relaxed text-text-primary text-sm space-y-4 font-light">
            {email.content.split("\n\n").map((paragraph, index) => (
              <p key={index} className="text-sm leading-relaxed">
                {paragraph}
              </p>
            ))}
          </div>

          {email.attachments && (
            <div className="p-4 border-t border-border-primary">
              <h4 className="font-medium text-xs text-text-tertiary uppercase mb-3 tracking-wider">
                Attachments
              </h4>
              {email.attachments.map((attachment, index) => (
                <div
                  key={index}
                  className="flex items-center p-2 bg-bg-tertiary border border-border-secondary rounded-xl hover:shadow-sm transition-all duration-200"
                >
                  <FileText className="text-danger-text text-2xl mr-3" />
                  <div className="flex-1">
                    <p className="font-medium text-sm text-text-primary">
                      {attachment.name}
                    </p>
                    <p className="text-xs text-text-tertiary mt-1">
                      {attachment.size}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="p-2 rounded-lg hover:bg-bg-primary text-text-tertiary hover:text-text-primary transition-colors">
                      <Download className="w-4 h-4" />
                    </button>
                    <button className="p-2 rounded-lg hover:bg-bg-primary text-text-tertiary hover:text-text-primary transition-colors">
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="p-4 border-t border-border-primary flex items-center space-x-3">
            <button
              onClick={e => {
                e.stopPropagation();
                if (onReply) onReply(email);
              }}
              className="flex-1 flex items-center justify-center px-4 py-2.5 text-xs font-medium text-accent-text bg-accent-primary rounded-xl hover:bg-accent-primary-hover transition-all duration-200 shadow-sm hover:shadow-md"
            >
              <Reply className="mr-2 w-4 h-4" /> Reply
            </button>
            {/* Removed Reply All button */}
            <button
              onClick={e => {
                e.stopPropagation();
                if (onForward) onForward(email);
              }}
              className="flex-1 flex items-center justify-center px-4 py-2.5 text-xs font-medium text-text-secondary border border-border-secondary rounded-xl hover:bg-bg-tertiary transition-all duration-200"
            >
              <Forward className="mr-2 w-4 h-4" /> Forward
            </button>
            <button
              onClick={e => {
                e.stopPropagation();
                if (onArchive) onArchive(email.id);
              }}
              className="flex-1 flex items-center justify-center px-4 py-2.5 text-xs font-medium text-text-secondary border border-border-secondary rounded-xl hover:bg-bg-tertiary transition-all duration-200"
            >
              <Archive className="mr-2 w-4 h-4" /> Archive
            </button>
            <button
              onClick={e => {
                e.stopPropagation();
                if (onDelete) onDelete(email.id);
              }}
              className="flex-1 flex items-center justify-center px-4 py-2.5 text-xs font-medium text-danger-text border border-danger-border rounded-xl hover:bg-danger-hover transition-all duration-200"
            >
              <Trash2 className="mr-2 w-4 h-4" /> Delete
            </button>
          </div>
        </div>
        <div className="p-4 border-t border-border-primary flex items-center justify-center">
          <button
            onClick={e => {
              e.stopPropagation();
              if (onAutoWrite) onAutoWrite(email);
            }}
            className="flex items-center px-3 py-2 text-xs font-medium text-accent-text bg-accent-primary rounded-full hover:bg-accent-primary-hover shadow-sm transition-all duration-200"
          >
            <Sparkles className="w-3 h-3 mr-2" />
            Auto Write
          </button>
        </div>
      </div>
    );
  };

  return (
    <div
      className={`bg-bg-primary rounded-lg shadow-sm border transition-all duration-200 hover:shadow-md ${
        isOpen ? "border-accent-primary shadow-lg" : "border-border-primary"
      }`}
    >
      <div
        onClick={onToggle}
        className="group p-4 cursor-pointer hover:bg-bg-tertiary/50 rounded-t-xl transition-all duration-200"
      >
        <div className="flex items-start space-x-3">
          {email.avatar ? (
            <img
              alt={`${email.sender} avatar`}
              className="w-10 h-10 rounded-full ring-2 ring-border-primary"
              src={email.avatar}
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center shrink-0 ring-2 ring-border-primary">
              {getEmailIcon(email.sender)}
            </div>
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center space-x-2 min-w-0 flex-1">
                <p className="font-semibold text-sm text-text-primary truncate">
                  {email.sender}
                </p>
                {/* Tags display beside sender name */}
                {isEditingTags ? (
                  <div className="flex items-center space-x-2 shrink-0">
                    <div className="flex items-center space-x-1">
                      {editingTags.map((tag, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center bg-accent-primary/10 text-accent-primary text-xs font-medium px-2 py-0.5 rounded-full border border-accent-primary/20"
                        >
                          {tag}
                          <button
                            onClick={e => {
                              e.stopPropagation();
                              handleRemoveTag(tag);
                            }}
                            className="ml-1 hover:bg-accent-primary/20 rounded-full p-0.5"
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                    <input
                      type="text"
                      value={newTagInput}
                      onChange={e => setNewTagInput(e.target.value)}
                      onKeyDown={handleKeyPress}
                      placeholder="Add tag..."
                      className="w-20 text-xs px-2 py-0.5 border border-border-secondary rounded-full bg-bg-primary text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent-primary"
                      onClick={e => e.stopPropagation()}
                    />
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        handleAddTag();
                      }}
                      className="p-1 rounded-full hover:bg-bg-tertiary text-text-tertiary hover:text-accent-primary"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        handleSaveTags();
                      }}
                      className="p-1 rounded-full hover:bg-bg-tertiary text-text-tertiary hover:text-green-600"
                    >
                      <Check className="w-3 h-3" />
                    </button>
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        handleCancelEdit();
                      }}
                      className="p-1 rounded-full hover:bg-bg-tertiary text-text-tertiary hover:text-red-600"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                ) : (
                  <>
                    {email.tags && email.tags.length > 0 && (
                      <div className="flex items-center space-x-1 shrink-0">
                        {email.tags.slice(0, 2).map((tag, index) => (
                          <span
                            key={index}
                            className="inline-block bg-accent-primary/10 text-accent-primary text-xs font-medium px-2 py-0.5 rounded-full border border-accent-primary/20"
                          >
                            {tag}
                          </span>
                        ))}
                        {email.tags.length > 2 && (
                          <span className="text-xs text-text-tertiary font-medium">
                            +{email.tags.length - 2}
                          </span>
                        )}
                      </div>
                    )}
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        setIsEditingTags(true);
                      }}
                      className="p-1 rounded-full hover:bg-bg-tertiary text-text-tertiary hover:text-accent-primary opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Edit3 className="w-3 h-3" />
                    </button>
                  </>
                )}
              </div>
              <div className="flex items-center space-x-2 shrink-0">
                <span className="text-xs text-text-tertiary font-medium">
                  {email.time}
                </span>
                <button
                  onClick={onToggleStar}
                  className="p-1 rounded-full hover:bg-bg-secondary transition-colors"
                >
                  {email.isStarred ? (
                    <Star className="w-4 h-4 fill-current text-yellow-500" />
                  ) : (
                    <StarOff className="w-4 h-4 text-gray-400 hover:text-yellow-500" />
                  )}
                </button>
              </div>
            </div>

            <div className="space-y-1">
              <p
                className={`text-sm font-medium truncate ${email.isRead ? "text-text-secondary" : "text-text-primary"}`}
              >
                {email.subject}
              </p>
              <p className="text-xs text-text-tertiary line-clamp-2 leading-relaxed">
                {email.preview}
              </p>
            </div>

            {email.hasAttachment && (
              <div className="flex items-center mt-2">
                <FileText className="w-3 h-3 text-text-tertiary mr-1" />
                <span className="text-xs text-text-tertiary">Attachment</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {isOpen && renderEmailContent()}
    </div>
  );
};

export default EmailCard;
