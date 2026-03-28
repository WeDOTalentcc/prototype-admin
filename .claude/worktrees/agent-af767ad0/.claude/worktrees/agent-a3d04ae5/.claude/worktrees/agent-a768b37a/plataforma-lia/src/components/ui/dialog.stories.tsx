import type { Meta, StoryObj } from '@storybook/nextjs-vite';
import { useState } from 'react';
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from './dialog';
import { Button } from './button';
import { Input } from './input';

const meta = {
  title: 'UI/Dialog',
  component: Dialog,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Dialog/Modal component built on Radix UI Dialog primitive.

## Design Standards
- **Background**: White with dark mode support (gray-950)
- **Overlay**: Black/40 with backdrop blur
- **Typography**:
  - Title: 12px, font-semibold
  - Description: 11px, gray-500
- **Animation**: Fade and zoom animations on open/close
- **Max width**: 512px (max-w-lg)
        `,
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Dialog>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>
            This is a description of the dialog. It provides context for the user.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p className="text-[11px] text-gray-800 dark:text-gray-200">Dialog content goes here.</p>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button>Confirm</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const WithForm: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Edit Profile</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
          <DialogDescription>
            Make changes to your profile here. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <label htmlFor="name" className="text-right text-[11px]">
              Name
            </label>
            <Input id="name" defaultValue="João Silva" className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <label htmlFor="email" className="text-right text-[11px]">
              Email
            </label>
            <Input id="email" defaultValue="joao@example.com" className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button className="bg-gray-900">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const Confirmation: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete Account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Are you sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete your account
            and remove your data from our servers.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="sm:justify-start">
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button variant="destructive">Yes, delete account</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const LargeContent: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">View Terms</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Terms of Service</DialogTitle>
          <DialogDescription>
            Please read our terms carefully before proceeding.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <p className="text-[11px] text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod 
            tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, 
            quis nostrud exercitation ullamco laboris.
          </p>
          <p className="text-[11px] text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore 
            eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, 
            sunt in culpa qui officia deserunt mollit anim id est laborum.
          </p>
          <p className="text-[11px] text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
            Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium 
            doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore 
            veritatis et quasi architecto beatae vitae dicta sunt explicabo.
          </p>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Decline</Button>
          </DialogClose>
          <Button>Accept</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const CandidateAction: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button className="bg-gray-900">Schedule Interview</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Schedule Interview</DialogTitle>
          <DialogDescription>
            Schedule an interview with the candidate. They will receive an email notification.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
            <div 
              className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold bg-gray-900"
            >
              JD
            </div>
            <div>
              <p className="text-xs font-semibold">João da Silva</p>
              <p className="text-[11px] text-gray-500">Senior Developer</p>
            </div>
          </div>
          <div className="grid gap-2">
            <label className="text-[11px] font-medium">Date & Time</label>
            <Input type="datetime-local" />
          </div>
          <div className="grid gap-2">
            <label className="text-[11px] font-medium">Interview Type</label>
            <select className="flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-[11px]">
              <option>Video Call</option>
              <option>Phone Call</option>
              <option>In Person</option>
            </select>
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button className="bg-gray-900">Schedule</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const Minimal: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="ghost">Info</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Quick Info</DialogTitle>
        </DialogHeader>
        <p className="text-[11px] text-gray-800 dark:text-gray-200 py-2">
          This is a minimal dialog with just a title and content.
        </p>
      </DialogContent>
    </Dialog>
  ),
};
