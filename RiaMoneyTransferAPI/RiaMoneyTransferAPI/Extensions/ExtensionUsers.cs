using RiaMoneyTransferAPI.Model;

namespace RiaMoneyTransferAPI.Extensions
{
    public static class ExtensionUsers
    {
        public static List<User> SortUser(this List<User> users)
        {
            for (int i = 0; i < users.Count; i++)
            {
                
                for (int j = i + 1; j < users.Count; j++)
                {
                    if (string.Compare(users[i].lastName, users[j].lastName) == 1)
                    {
                        User tempUser = users[i];
                        users[i] = users[j];
                        users[j] = tempUser;

                    }
                    else if (string.Compare(users[i].lastName, users[j].lastName) == 0 &&
                        string.Compare(users[i].firstName, users[j].firstName) == 1)
                    {
                        User tempUser = users[i];
                        users[i] = users[j];
                        users[j] = tempUser;

                    }
                }
            }

            //users.Sort(compareTo);
            return users;
        }


        public static bool ContainsUserbyId(this List<User> users, int id)
        { 
            var user =users.Where(o=>o.id == id).FirstOrDefault();

            return user != null;
        
        }

        public static int compareTo(User user, User other)
        {

            if (string.IsNullOrEmpty(user.lastName))
            { 
                if (string.IsNullOrEmpty(other.lastName))
                    return 0;
                else
                    return -1;

            }
            else
            { 
                if (string.IsNullOrEmpty(other.lastName))
                return 1;
                else
                    if(user.lastName.CompareTo(other.lastName)!=0)
                        return user.lastName.CompareTo(other.lastName);
            }

            if (string.IsNullOrEmpty(user.firstName))
                if (string.IsNullOrEmpty(other.firstName))
                    return 0;
                else
                    return -1;
            else
                if (string.IsNullOrEmpty(other.firstName))
                return 1;
            else
                return user.lastName.CompareTo(other.firstName);

        }
    }
}
