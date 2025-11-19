import React from 'react';
import { FaEdit, FaEye, FaTrash } from 'react-icons/fa';
import { Loader2 } from 'lucide-react';

const UserList = ({ users, onViewUser, onEditUser, onDeleteUser, loading, deleteLoading, updateLoading, userDetailsLoading, formatDate, getUserStatusColor }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
              User Name
            </th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
              Contact
            </th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
              Location
            </th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
              Status
            </th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
              Date Added
            </th>
            <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center">
                  <div className="ml-4">
                    <div className="text-sm font-medium text-gray-900">
                      {user.username || user.name || 'N/A'}
                    </div>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{user.email || 'N/A'}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">
                  Block: {user.blockBuilding || user.block || 'N/A'}
                </div>
                <div className="text-sm text-gray-500">
                  Floor: {user.floor || 'N/A'}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {(() => {
                  const status = (user.is_active === true) ? 'Active' : (user.is_active === false ? 'Inactive' : (user.status || 'Active'));
                  return (
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getUserStatusColor(status)}`}>
                      {status}
                    </span>
                  );
                })()}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                {formatDate(user.dateAdded || user.created_at)}
              </td>
              <td className="px-6 py-4 text-sm font-medium whitespace-nowrap">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onViewUser(user)}
                    disabled={userDetailsLoading[user.id]}
                    className="flex items-center p-1 text-blue-600 transition-colors rounded-md hover:bg-blue-100 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="View User Details"
                  >
                    {userDetailsLoading[user.id] ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <FaEye className="w-3 h-3" />
                    )}
                  </button>
                  <button
                    onClick={() => onEditUser(user)}
                    disabled={updateLoading[user.id]}
                    className="flex items-center p-1 text-gray-500 transition-colors rounded-md hover:bg-gray-100 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Edit User"
                  >
                    {updateLoading[user.id] ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <FaEdit className="w-3 h-3" />
                    )}
                  </button>
                  <button
                    onClick={() => onDeleteUser(user)}
                    disabled={deleteLoading[user.id]}
                    className="flex items-center p-1 text-red-500 transition-colors rounded-md hover:bg-red-100 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Delete User"
                  >
                    {deleteLoading[user.id] ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <FaTrash className="w-3 h-3" />
                    )}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default UserList;
