import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useStore } from '../store/useStore'
import { supabase } from '../lib/supabase'

export default function ListPage() {
  const { listId } = useParams<{ listId: string }>()
  const navigate = useNavigate()
  const { currentList, items, setCurrentList, setItems, addItem, toggleItem, deleteItem } = useStore()
  const [newItemName, setNewItemName] = useState('')

  useEffect(() => {
    if (!listId) return
    loadList()
    loadItems()

    // Subscribe to real-time updates
    const channel = supabase
      .channel(`list-${listId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'items',
          filter: `list_id=eq.${listId}`
        },
        () => {
          loadItems()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [listId])

  const loadList = async () => {
    if (!listId) return

    const { data, error } = await supabase
      .from('lists')
      .select('*')
      .eq('id', listId)
      .single()

    if (error) {
      console.error('Error loading list:', error)
      return
    }

    setCurrentList(data)
  }

  const loadItems = async () => {
    if (!listId) return

    const { data, error } = await supabase
      .from('items')
      .select('*')
      .eq('list_id', listId)
      .order('position', { ascending: true })

    if (error) {
      console.error('Error loading items:', error)
      return
    }

    setItems(data || [])
  }

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newItemName.trim() || !listId) return

    try {
      await addItem({
        list_id: listId,
        name: newItemName,
        category: null,
        checked: false,
        position: items.length,
        checked_at: null
      })
      setNewItemName('')
    } catch (error) {
      console.error('Error adding item:', error)
    }
  }

  const handleToggle = async (id: string) => {
    try {
      await toggleItem(id)
    } catch (error) {
      console.error('Error toggling item:', error)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteItem(id)
    } catch (error) {
      console.error('Error deleting item:', error)
    }
  }

  const uncheckedItems = items.filter(item => !item.checked)
  const checkedItems = items.filter(item => item.checked)

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="mb-6">
        <button onClick={() => navigate('/')} className="text-blue-600 mb-2">
          ← Back to Lists
        </button>
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">{currentList?.name || 'Loading...'}</h1>
          <button
            onClick={() => navigate(`/list/${listId}/shop`)}
            className="btn-primary"
          >
            Shopping Mode
          </button>
        </div>
      </div>

      <form onSubmit={handleAddItem} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
            placeholder="Add item..."
            className="input-field flex-1"
          />
          <button type="submit" className="btn-primary">
            Add
          </button>
        </div>
      </form>

      <div className="space-y-4">
        {/* Unchecked items */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="font-semibold text-lg mb-3">To Buy ({uncheckedItems.length})</h2>
          <div className="space-y-2">
            {uncheckedItems.map((item) => (
              <div key={item.id} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded">
                <input
                  type="checkbox"
                  checked={item.checked}
                  onChange={() => handleToggle(item.id)}
                  className="w-5 h-5 cursor-pointer"
                />
                <span className="flex-1">{item.name}</span>
                <button
                  onClick={() => handleDelete(item.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  Delete
                </button>
              </div>
            ))}
            {uncheckedItems.length === 0 && (
              <p className="text-gray-400 text-center py-4">No items yet</p>
            )}
          </div>
        </div>

        {/* Checked items */}
        {checkedItems.length > 0 && (
          <div className="bg-white rounded-lg shadow p-4">
            <h2 className="font-semibold text-lg mb-3">Completed ({checkedItems.length})</h2>
            <div className="space-y-2">
              {checkedItems.map((item) => (
                <div key={item.id} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded opacity-60">
                  <input
                    type="checkbox"
                    checked={item.checked}
                    onChange={() => handleToggle(item.id)}
                    className="w-5 h-5 cursor-pointer"
                  />
                  <span className="flex-1 line-through">{item.name}</span>
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-red-600 hover:text-red-800 text-sm"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
