using RiaMoneyTransferAPI.Extensions;
using RiaMoneyTransferAPI.Model;

namespace RiaMoneyTransferAPI.Service
{
    public class UserService : IUserService
    {
        private List<User> _users = new List<User>()
        {

            new User(){ lastName= "Aaaa", firstName= "Aaaa", age= 20, id= 3 },
            new User(){ lastName= "Aaaa", firstName= "Bbbb", age= 56, id= 2 },
            new User(){ lastName= "Cccc", firstName= "Aaaa", age= 32, id= 5 },
            new User(){ lastName= "Cccc", firstName= "Bbbb", age= 50, id= 1 },
            new User(){ lastName= "Dddd", firstName= "Aaaa", age= 70, id= 4 }


        };
        
        public bool AddUser(User user)
        {
            _users=_users.SortUser();
            bool isInserted = false;

            if (_users.ContainsUserbyId(user.id))
            {
                return isInserted;
            }

            int maxCount=_users.Count();

            for (int i = 0,a=0; i < _users.Count; i++,a++)
            {
                int v = string.Compare(_users[i].lastName, user.lastName);
                int c = string.Compare(_users[i].firstName,user.firstName);
                if (v==1||(c==1 && v==0))
                {
                    if (user.id != maxCount + 1)
                    {
                        user.id = maxCount + 1;
                    }
                    _users.Insert(a, user); isInserted = true;maxCount++;
                    break;
                }
            
            }

            if (!isInserted)
            { 
                _users.Add(user); isInserted = true;
            }
            return isInserted;

           
        }

        public void AddUsers(User[] users)
        {

            for (int i = 0; i < users.Length; i++)
            {
                Console.WriteLine($"Is user inserted with user id: {users[i].id} : {AddUser(users[i])}" );
            }
        
        }


        public List<User> GetUsers()
        {
            //_users = _users.SortUser();
            return _users;
        }
    }
}
