using RiaMoneyTransferAPI.Model;

namespace RiaMoneyTransferAPI.Service
{
    public interface IUserService
    {
        public List<User> GetUsers();

        public bool AddUser(User user);

        public void AddUsers(User []users);
    }
}
