import { create } from 'zustand'
import { supabase } from '../lib/supabase'
import type { User } from '@supabase/supabase-js'

export interface GroceryItem {
  id: string
  list_id: string
  name: string
  category: string | null
  checked: boolean
  position: number
  checked_at: string | null
  created_at: string
}

export interface GroceryList {
  id: string
  user_id: string
  name: string
  created_at: string
  updated_at: string
}

interface StoreState {
  user: User | null
  lists: GroceryList[]
  currentList: GroceryList | null
  items: GroceryItem[]
  isOnline: boolean

  // Actions
  setUser: (user: User | null) => void
  setLists: (lists: GroceryList[]) => void
  setCurrentList: (list: GroceryList | null) => void
  setItems: (items: GroceryItem[]) => void
  setOnlineStatus: (status: boolean) => void

  addItem: (item: Omit<GroceryItem, 'id' | 'created_at'>) => Promise<void>
  updateItem: (id: string, updates: Partial<GroceryItem>) => Promise<void>
  deleteItem: (id: string) => Promise<void>
  toggleItem: (id: string) => Promise<void>
}

export const useStore = create<StoreState>((set, get) => ({
  user: null,
  lists: [],
  currentList: null,
  items: [],
  isOnline: navigator.onLine,

  setUser: (user) => set({ user }),
  setLists: (lists) => set({ lists }),
  setCurrentList: (list) => set({ currentList: list }),
  setItems: (items) => set({ items }),
  setOnlineStatus: (status) => set({ isOnline: status }),

  addItem: async (item) => {
    const { data, error } = await supabase
      .from('items')
      .insert([item])
      .select()
      .single()

    if (error) throw error

    set((state) => ({
      items: [...state.items, data]
    }))
  },

  updateItem: async (id, updates) => {
    const { data, error } = await supabase
      .from('items')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) throw error

    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, ...data } : item
      )
    }))
  },

  deleteItem: async (id) => {
    const { error } = await supabase
      .from('items')
      .delete()
      .eq('id', id)

    if (error) throw error

    set((state) => ({
      items: state.items.filter((item) => item.id !== id)
    }))
  },

  toggleItem: async (id) => {
    const item = get().items.find((i) => i.id === id)
    if (!item) return

    const updates = {
      checked: !item.checked,
      checked_at: !item.checked ? new Date().toISOString() : null
    }

    await get().updateItem(id, updates)
  }
}))
