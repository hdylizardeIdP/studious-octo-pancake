import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStore } from '../store/useStore'
import { supabase } from '../lib/supabase'

export default function HomePage() {
  const navigate = useNavigate()
  const { user, lists, setUser, setLists } = useStore()
  const [newListName, setNewListName] = useState('')

  useEffect(() => {
    // Check auth session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
    })

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [setUser])

  useEffect(() => {
    if (user) {
      loadLists()
    }
  }, [user])

  const loadLists = async () => {
    const { data, error } = await supabase
      .from('lists')
      .select('*')
      .order('updated_at', { ascending: false })

    if (error) {
      console.error('Error loading lists:', error)
      return
    }

    setLists(data || [])
  }

  const createList = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newListName.trim() || !user) return

    const { data, error } = await supabase
      .from('lists')
      .insert([{ name: newListName, user_id: user.id }])
      .select()
      .single()

    if (error) {
      console.error('Error creating list:', error)
      return
    }

    setNewListName('')
    loadLists()
    navigate(`/list/${data.id}`)
  }

  const signIn = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
    })
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">Grocery List</h1>
          <p className="text-gray-600 mb-8">Smart shopping list with offline support</p>
          <button onClick={signIn} className="btn-primary">
            Sign In with Google
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">My Lists</h1>
        <p className="text-gray-600">Create and manage your grocery lists</p>
      </div>

      <form onSubmit={createList} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={newListName}
            onChange={(e) => setNewListName(e.target.value)}
            placeholder="New list name..."
            className="input-field flex-1"
          />
          <button type="submit" className="btn-primary">
            Create List
          </button>
        </div>
      </form>

      <div className="space-y-2">
        {lists.map((list) => (
          <div
            key={list.id}
            onClick={() => navigate(`/list/${list.id}`)}
            className="p-4 bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
          >
            <h3 className="font-semibold">{list.name}</h3>
            <p className="text-sm text-gray-500">
              Updated {new Date(list.updated_at).toLocaleDateString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
