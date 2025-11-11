import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Database = {
  public: {
    Tables: {
      lists: {
        Row: {
          id: string
          user_id: string
          name: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          created_at?: string
          updated_at?: string
        }
      }
      items: {
        Row: {
          id: string
          list_id: string
          name: string
          category: string | null
          checked: boolean
          position: number
          checked_at: string | null
          created_at: string
        }
        Insert: {
          id?: string
          list_id: string
          name: string
          category?: string | null
          checked?: boolean
          position?: number
          checked_at?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          list_id?: string
          name?: string
          category?: string | null
          checked?: boolean
          position?: number
          checked_at?: string | null
          created_at?: string
        }
      }
      list_members: {
        Row: {
          list_id: string
          user_id: string
          role: string
          created_at: string
        }
        Insert: {
          list_id: string
          user_id: string
          role?: string
          created_at?: string
        }
        Update: {
          list_id?: string
          user_id?: string
          role?: string
          created_at?: string
        }
      }
    }
  }
}
