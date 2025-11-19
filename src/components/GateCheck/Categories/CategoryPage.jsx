import React, { useState, useEffect } from "react";
import { Plus, Loader, FolderOpen, Search, RefreshCw } from "lucide-react";
import { api } from '../../Auth/api';
import CategoryTable from './CategoryTable';
import CategoryModal from './CategoryModal';
import AlertMessage from './AlertMessage';
import StatsCards from './StatsCards';

const CategoryPage = (props) => {
  // Accept setCategoryCount as a prop
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [filterActive, setFilterActive] = useState("all");
  const [submitting, setSubmitting] = useState(false);
  const [newCategory, setNewCategory] = useState({
    name: "",
    description: "",
    is_active: true
  });

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.categories.getAll();
      setCategories(response.data);
      // Update category count in App.js if prop exists
      if (typeof props.setCategoryCount === 'function') {
        props.setCategoryCount(response.data.length);
      }
      console.log(response.data);
    } catch (err) {
      console.error('Error fetching categories:', err);
      setError('Failed to load categories. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCategory = async () => {
    if (!newCategory.name.trim()) {
      alert('Please enter a category name');
      return;
    }
    try {
      setSubmitting(true);
      const response = await api.categories.create(newCategory);
      setCategories([...categories, response.data]);
      setNewCategory({ name: "", description: "", is_active: true });
      setShowAddModal(false);
      setError(null);
    } catch (err) {
      console.error('Error creating category:', err);
      setError(err.response?.data?.message || 'Failed to create category');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditCategory = async () => {
    if (!selectedCategory || !selectedCategory.name.trim()) {
      alert('Please enter a category name');
      return;
    }
    try {
      setSubmitting(true);
      const response = await api.categories.update(selectedCategory.id, selectedCategory);
      setCategories(categories.map(category =>
        category.id === selectedCategory.id ? response.data : category
      ));
      setShowEditModal(false);
      setSelectedCategory(null);
      setError(null);
    } catch (err) {
      console.error('Error updating category:', err);
      setError(err.response?.data?.message || 'Failed to update category');
    } finally {
      setSubmitting(false);
    }
  };

  // Delete logic removed as per requirements

  const toggleCategoryStatus = async (categoryId) => {
    const category = categories.find(c => c.id === categoryId);
    if (!category) return;
    try {
      const updatedCategory = { ...category, is_active: !category.is_active };
      const response = await api.categories.update(categoryId, updatedCategory);
      setCategories(categories.map(c =>
        c.id === categoryId ? response.data : c
      ));
      setError(null);
    } catch (err) {
      console.error('Error updating category status:', err);
      setError(err.response?.data?.message || 'Failed to update category status');
    }
  };

  const filteredCategories = categories.filter(category => {
    const matchesSearch = category.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         category.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterActive === "all" ||
                         (filterActive === "active" && category.is_active) ||
                         (filterActive === "inactive" && !category.is_active);
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen p-6 bg-gray-50">
        <div className="text-center">
          <Loader className="mx-auto mb-4 text-purple-600 animate-spin" size={48} />
          <p className="text-gray-600">Loading categories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen pl-4 bg-gray-50">
      <div className="mx-auto max-w-7xl">
        <div className="mb-2">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="flex items-center gap-2 text-3xl font-bold text-gray-900">
                <FolderOpen className="text-purple-600" size={32} />
                Categories Management
              </h1>
              <p className="mt-1 text-gray-600">Manage visitor categories and types</p>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 p-2 text-purple-800 transition-colors bg-transparent border border-purple-800 rounded-lg hover:bg-purple-100"
            >
              <Plus size={20} />
              Add Category
            </button>
          </div>
        </div>

        <AlertMessage message={error} type="error" />

        <StatsCards categories={categories} />

        <div className="p-2 mb-6 bg-white border rounded-lg shadow-sm">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute text-gray-400 transform -translate-y-1/2 left-3 top-1/2" size={15} />
                <input
                  type="text"
                  placeholder="Search categories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="p-2 pl-8 text-sm border border-gray-300 outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <select
                value={filterActive}
                onChange={(e) => setFilterActive(e.target.value)}
                className="p-2 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="all">All Categories</option>
                <option value="active">Active Only</option>
                <option value="inactive">Inactive Only</option>
              </select>
            </div>
            <button
              onClick={fetchCategories}
              className="flex items-center px-3 py-2 text-purple-600 rounded-lg bg-purple-50 hover:bg-purple-100 disabled:opacity-50"
            >
              <RefreshCw className='w-4 h-4 mr-2' />
              Refresh
            </button>
          </div>
        </div>

        <CategoryTable
          categories={filteredCategories}
          onEdit={setSelectedCategory}
          onShowEditModal={setShowEditModal}
          onToggleStatus={toggleCategoryStatus}
        />

        <CategoryModal
          isOpen={showAddModal}
          onClose={() => setShowAddModal(false)}
          title="Add New Category"
          category={newCategory}
          onChange={setNewCategory}
          onSubmit={handleAddCategory}
          submitting={submitting}
        />

        <CategoryModal
          isOpen={showEditModal}
          onClose={() => setShowEditModal(false)}
          title="Edit Category"
          category={selectedCategory}
          onChange={setSelectedCategory}
          onSubmit={handleEditCategory}
          submitting={submitting}
        />
      </div>
    </div>
  );
};

export default CategoryPage;