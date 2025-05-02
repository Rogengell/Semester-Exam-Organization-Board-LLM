using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Linq;
using System.Threading.Tasks;

namespace EFrameWork.Model
{
    public class UserToTask
    {
                
        [Key]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int UserToTaskID { get; set; }

        [Required]
        public int UserID { get; set; }

        [ForeignKey("UserID")]
        public User User { get; set; }

        [Required]
        public int TaskID { get; set; }

        [ForeignKey("TaskID")]
        public Task Task { get; set; }
    }
}