type ScanJob = {
  id: string;
  target: string;
  profile: string;
  status: string;
  createdAt?: string;
  finishedAt?: string | null;
};

type Props = {
  scans: ScanJob[];
  onSelectJob: (id: string) => void;
};

export default function ScanTable({ scans, onSelectJob }: Props) {
  return (
    <table className="table-auto w-full text-left border-collapse">
      <thead>
        <tr>
          <th className="border-b border-gray-700 px-2 py-1">Job ID</th>
          <th className="border-b border-gray-700 px-2 py-1">Target</th>
          <th className="border-b border-gray-700 px-2 py-1">Profile</th>
          <th className="border-b border-gray-700 px-2 py-1">Status</th>
          <th className="border-b border-gray-700 px-2 py-1">Created</th>
          <th className="border-b border-gray-700 px-2 py-1">Actions</th>
        </tr>
      </thead>
      <tbody>
        {scans.map((scan) => (
          <tr key={scan.id}>
            <td className="border-b border-gray-800 px-2 py-1">{scan.id}</td>
            <td className="border-b border-gray-800 px-2 py-1">{scan.target}</td>
            <td className="border-b border-gray-800 px-2 py-1">{scan.profile}</td>
            <td className="border-b border-gray-800 px-2 py-1">{scan.status}</td>
            <td className="border-b border-gray-800 px-2 py-1">
              {scan.createdAt
                ? new Date(scan.createdAt).toLocaleString()
                : ""}
            </td>
            <td className="border-b border-gray-800 px-2 py-1">
              <button
                className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded"
                onClick={() => onSelectJob(scan.id)}
              >
                View Results
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
