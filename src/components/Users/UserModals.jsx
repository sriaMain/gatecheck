import React from 'react';
import { FaTimes, FaExclamationTriangle, FaSave, FaTrash } from 'react-icons/fa';
import { Loader2 } from 'lucide-react';

const UserModals = ({
  showViewModal,
  showEditModal,
  showDeleteModal,
  selectedUser,
  editFormData,
  onClose,
  onInputChange,
  onSaveUser,
  onDeleteUser,
  updateLoading,
  deleteLoading,
  getUserStatusColor,
  formatDate
}) => {
  return (
    <>
      {showViewModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800">User Details</h3>
              <button
                onClick={onClose}
                className="text-gray-400 transition-colors hover:text-gray-600"
              >
                <FaTimes className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Name</label>
                <p className="text-sm text-gray-900">{selectedUser.username || selectedUser.name || 'N/A'}</p>
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Email</label>
                <p className="text-sm text-gray-900">{selectedUser.email || 'N/A'}</p>
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Block/Building</label>
                <p className="text-sm text-gray-900">{selectedUser.blockBuilding || selectedUser.block || 'N/A'}</p>
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Floor</label>
                <p className="text-sm text-gray-900">{selectedUser.floor || 'N/A'}</p>
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Status</label>
                {(() => {
                  const status = (selectedUser.is_active === true) ? 'Active' : (selectedUser.is_active === false ? 'Inactive' : (selectedUser.status || 'Active'));
                  return (
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getUserStatusColor(status)}`}>
                      {status}
                    </span>
                  );
                })()}
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Date Added</label>
                <p className="text-sm text-gray-900">{formatDate(selectedUser.dateAdded || selectedUser.created_at)}</p>
              </div>
            </div>
            <div className="flex justify-end p-6 border-t border-gray-200">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {showEditModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800">Edit User</h3>
              <button
                onClick={onClose}
                className="text-gray-400 transition-colors hover:text-gray-600"
              >
                <FaTimes className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  name="username"
                  value={editFormData.username}
                  onChange={onInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Email</label>
                <input
                  type="email"
                  name="email"
                  value={editFormData.email}
                  onChange={onInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Block/Building</label>
                <input
                  type="text"
                  name="block"
                  value={editFormData.block}
                  onChange={onInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block mb-1 text-sm font-medium text-gray-700">Floor</label>
                <input
                  type="text"
                  name="floor"
                  value={editFormData.floor}
                  onChange={onInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={!!editFormData.is_active}
                    onChange={onInputChange}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Active</span>
                </label>
              </div>
            </div>
            <div className="flex justify-end p-6 space-x-3 border-t border-gray-200">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Cancel
              </button>
              <button
                onClick={onSaveUser}
                disabled={updateLoading[selectedUser.id]}
                className="flex items-center px-4 py-2 text-sm font-medium text-purple-800 bg-transparent border border-purple-800 rounded-md hover:bg-purple-100 focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {updateLoading[selectedUser.id] ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <FaSave className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      {showDeleteModal && selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md mx-4 bg-white rounded-lg shadow-xl">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800">Confirm Delete</h3>
              <button
                onClick={onClose}
                className="text-gray-400 transition-colors hover:text-gray-600"
              >
                <FaTimes className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full">
                  <FaExclamationTriangle className="w-6 h-6 text-red-600" />
                </div>
                <div className="ml-4">
                  <h4 className="text-lg font-medium text-gray-900">Delete User</h4>
                  <p className="text-sm text-gray-500">This action cannot be undone</p>
                </div>
              </div>
              <p className="mb-4 text-sm text-gray-700">
                Are you sure you want to delete <strong>{selectedUser.username || selectedUser.name || 'this user'}</strong>?
                This will permanently remove the user from the organization and cannot be undone.
              </p>
              <div className="p-3 border border-red-200 rounded-md bg-red-50">
                <div className="flex">
                  <FaExclamationTriangle className="w-5 h-5 text-red-400 mt-0.5" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">Warning</h3>
                    <div className="mt-1 text-sm text-red-700">
                      <p>This action will:</p>
                      <ul className="mt-1 list-disc list-inside">
                        <li>Remove the user from this organization</li>
                        <li>Delete all associated user data</li>
                        <li>Cannot be reversed</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex justify-end p-6 space-x-3 border-t border-gray-200">
              <button
                onClick={onClose}
                disabled={deleteLoading[selectedUser.id]}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={onDeleteUser}
                disabled={deleteLoading[selectedUser.id]}
                className="flex items-center px-4 py-2 text-sm font-medium text-red-600 bg-transparent border border-red-600 rounded-md hover:bg-red-100 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deleteLoading[selectedUser.id] ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <FaTrash className="w-4 h-4 mr-2" />
                    Delete User
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default UserModals;
