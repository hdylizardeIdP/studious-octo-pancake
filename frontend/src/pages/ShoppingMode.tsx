import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useStore } from '../store/useStore'
import { supabase } from '../lib/supabase'

export default function ShoppingMode() {
  const { listId } = useParams<{ listId: string }>()
  const navigate = useNavigate()
  const { currentList, items, setCurrentList, setItems, toggleItem } = useStore()

  useEffect(() => {
    if (!listId) return
    loadList()
    loadItems()

    // Subscribe to real-time updates
    const channel = supabase
      .channel(`shopping-${listId}`)
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

  const handleToggle = async (id: string) => {
    try {
      await toggleItem(id)
    } catch (error) {
      console.error('Error toggling item:', error)
    }
  }

  const uncheckedItems = items.filter(item => !item.checked)
  const checkedItems = items.filter(item => item.checked)
  const progress = items.length > 0 ? (checkedItems.length / items.length) * 100 : 0

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 p-4 sticky top-0 z-10">
        <button
          onClick={() => navigate(`/list/${listId}`)}
          className="text-blue-400 mb-2"
        >
          ← Exit Shopping Mode
        </button>
        <h1 className="text-2xl font-bold mb-2">{currentList?.name}</h1>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-700 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-sm">
            {checkedItems.length}/{items.length}
          </span>
        </div>
      </div>

      {/* Items to buy */}
      <div className="p-4">
        {uncheckedItems.length > 0 ? (
          <div className="space-y-3">
            {uncheckedItems.map((item) => (
              <div
                key={item.id}
                onClick={() => handleToggle(item.id)}
                className="bg-gray-800 p-5 rounded-lg flex items-center gap-4 active:bg-gray-700 cursor-pointer"
              >
                <div className="w-8 h-8 rounded-full border-2 border-gray-400 flex-shrink-0" />
                <span className="text-xl flex-1">{item.name}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold mb-2">All Done!</h2>
            <p className="text-gray-400 mb-6">You've checked off everything</p>
            <button
              onClick={() => navigate(`/list/${listId}`)}
              className="btn-primary"
            >
              Back to List
            </button>
          </div>
        )}

        {/* Completed items section */}
        {checkedItems.length > 0 && uncheckedItems.length > 0 && (
          <div className="mt-8 pt-6 border-t border-gray-700">
            <h3 className="text-gray-400 text-sm mb-3">COMPLETED</h3>
            <div className="space-y-2 opacity-50">
              {checkedItems.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleToggle(item.id)}
                  className="bg-gray-800 p-4 rounded-lg flex items-center gap-4 cursor-pointer"
                >
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-sm">✓</span>
                  </div>
                  <span className="line-through">{item.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
