"use client"
import React from "react"
import { UserCheck, Star, Zap, Heart, Target } from "lucide-react"

export const getCategoryIcon = (category: string) => {
  switch (category) {
    case "recruitment": return React.createElement(UserCheck, { className: "w-3 h-3 lia-text-500" })
    case "quality": return React.createElement(Star, { className: "w-3 h-3 lia-text-500" })
    case "efficiency": return React.createElement(Zap, { className: "w-3 h-3 lia-text-500" })
    case "satisfaction": return React.createElement(Heart, { className: "w-3 h-3 lia-text-500" })
    default: return React.createElement(Target, { className: "w-3 h-3 lia-text-500" })
  }
}

export const getCategoryColor = (category: string) => {
  switch (category) {
    case "recruitment": return "bg-gray-100 lia-text-700 border-lia-border-default"
    case "quality": return "bg-status-warning/10 text-status-warning border-status-warning/30"
    case "efficiency": return "bg-status-success/10 text-status-success border-status-success/30"
    case "satisfaction": return "bg-gray-100 lia-text-700 dark:bg-lia-bg-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-subtle"
    default: return "bg-gray-100 lia-text-800 dark:text-lia-text-primary border-lia-border-subtle"
  }
}

export const getStatusColor = (status: string) => {
  switch (status) {
    case "achieved": return "bg-status-success/15 text-status-success border-status-success/30"
    case "in_progress": return "bg-status-warning/10 text-status-warning border-status-warning/30"
    case "overdue": return "bg-status-error/15 text-status-error border-status-error/30"
    default: return "bg-gray-100 lia-text-800 dark:text-lia-text-primary border-lia-border-subtle"
  }
}
